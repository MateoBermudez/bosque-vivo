from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from bosquevivo.ai.agent import Agent, AgentRequest
from bosquevivo.ai.agent.resolver import ProjectResolver
from bosquevivo.ai.llm import LLMProvider, MediaPart
from bosquevivo.assistant import texts
from bosquevivo.assistant.client import WhatsAppClient
from bosquevivo.assistant.community import (
    alerts_message,
    index_message,
    portfolio_message,
    status_message,
)
from bosquevivo.assistant.dialogue import (
    detect_intent,
    detect_portfolio,
    detect_topic,
    is_authorized,
    is_short_topic,
    refers_to_project,
    registered_project_id,
    split_message,
    wants_consent,
    wants_deletion,
    wants_media_consent,
)
from bosquevivo.assistant.messages import IncomingMessage
from bosquevivo.assistant.suggestions import CONSENT, NO_PROJECT, START, WITH_PROJECT
from bosquevivo.assistant.voice import transcribe_audio
from bosquevivo.core.config import Settings
from bosquevivo.core.errors import ExternalServiceError
from bosquevivo.core.logging import get_logger
from bosquevivo.core.privacy import phone_hmac
from bosquevivo.db.models import (
    AgentRun,
    ConsentLog,
    Evidence,
    ProcessedMessage,
    Project,
    WaUser,
)
from bosquevivo.registry.repository import ProjectRepository

log = get_logger(__name__)

PURPOSE_DATA = "datos"
PURPOSE_MEDIA = "medios"
EXACT_TOPICS = {"alertas", "estado"}
FIXED_REPLIES = {"ayuda": texts.HELP, "gracias": texts.THANKS, "quien": texts.ABOUT}
TOPIC_REPLIES = {
    "alertas": alerts_message,
    "estado": status_message,
    "indice": index_message,
}


class AssistantService:
    def __init__(
        self,
        session: Session,
        agent: Agent,
        client: WhatsAppClient,
        llm: LLMProvider,
        settings: Settings,
    ) -> None:
        self.session = session
        self.agent = agent
        self.client = client
        self.llm = llm
        self.settings = settings
        self.turn_project_id: int | None = None
        self.turn_choices: tuple[tuple[int, str], ...] = ()

    def already_processed(self, message_id: str) -> bool:
        return self.session.get(ProcessedMessage, message_id) is not None

    def mark_processed(self, message_id: str) -> bool:
        if self.already_processed(message_id):
            return False
        self.session.add(ProcessedMessage(message_id=message_id))
        self.session.flush()
        return True

    def _reply(self, phone: str, text: str) -> None:
        for chunk in split_message(text, self.settings.community_max_chars):
            self.client.send_text(phone, chunk)

    def _granted(self, user: WaUser, purpose: str) -> bool:
        latest = self.session.scalars(
            select(ConsentLog)
            .where(ConsentLog.user_id == user.id, ConsentLog.purpose == purpose)
            .order_by(ConsentLog.id.desc())
        ).first()
        return bool(latest and latest.granted)

    def _grant(self, user: WaUser, purpose: str) -> None:
        self.session.add(
            ConsentLog(
                user_id=user.id, purpose=purpose, notice_version=texts.NOTICE_VERSION, granted=True
            )
        )
        self.session.flush()

    def _user(self, phone: str) -> tuple[WaUser, bool]:
        digest = phone_hmac(phone, self.settings.phone_hmac_key)
        user = self.session.scalars(select(WaUser).where(WaUser.phone_hmac == digest)).first()
        if user:
            return user, False
        user = WaUser(phone_hmac=digest)
        self.session.add(user)
        self.session.flush()
        return user, True

    def delete_user(self, phone: str) -> None:
        digest = phone_hmac(phone, self.settings.phone_hmac_key)
        run_ids = self.session.scalars(select(AgentRun.id).where(AgentRun.user_ref == digest)).all()
        for run_id in run_ids:
            self.session.execute(
                delete(Evidence).where(Evidence.id.like(f"r{run_id}\\_%", escape="\\"))
            )
        self.session.execute(delete(AgentRun).where(AgentRun.user_ref == digest))
        user = self.session.scalars(select(WaUser).where(WaUser.phone_hmac == digest)).first()
        if user:
            self.session.delete(user)
        self.session.flush()

    def handle(self, message: IncomingMessage) -> None:
        self.turn_project_id = None
        self.turn_choices = ()
        if not self.mark_processed(message.message_id):
            return
        user = self._admit(message)
        if user is None:
            return
        phone = message.phone
        if wants_media_consent(message.text):
            self._grant(user, PURPOSE_MEDIA)
            self._reply(phone, texts.MEDIA_GRANTED)
            return
        if message.kind == "text":
            reply = self._intent_reply(user, message.text)
            if reply is not None:
                self._reply(phone, reply)
                return
        if message.kind == "location" and message.latitude is not None:
            self._reply(
                phone, self._register_by_location(user, message.latitude, message.longitude or 0.0)
            )
            return
        self._respond(user, message)

    def _admit(self, message: IncomingMessage) -> WaUser | None:
        phone = message.phone
        reply: str | None = None
        user: WaUser | None = None
        if not is_authorized(phone, self.settings.whatsapp_allowed_phones):
            log.info("whatsapp_unauthorized")
            reply = texts.NOT_AUTHORIZED
        elif wants_deletion(message.text):
            self.delete_user(phone)
            reply = texts.DELETED
        else:
            user, created = self._user(phone)
            if created:
                self._reply(phone, texts.WELCOME)
                reply = texts.NOTICE
            elif wants_consent(message.text):
                self._grant(user, PURPOSE_DATA)
                reply = texts.CONSENT_GRANTED
            elif not self._granted(user, PURPOSE_DATA):
                reply = texts.CONSENT_PENDING
        if reply is not None:
            self._reply(phone, reply)
            return None
        return user

    def _project_of(self, user: WaUser) -> Project | None:
        return self.session.get(Project, user.project_id) if user.project_id else None

    def _intent_reply(self, user: WaUser, text: str | None) -> str | None:
        intent = detect_intent(text)
        if intent in FIXED_REPLIES:
            return FIXED_REPLIES[intent]
        if intent == "saludo":
            return self._greeting(user)
        if intent == "registro":
            return self._register(user, registered_project_id(text) or 0)
        portfolio = detect_portfolio(text)
        if portfolio is not None:
            return portfolio_message(self.session, portfolio)
        return self._topic_reply(user, text or "", intent)

    def _greeting(self, user: WaUser) -> str:
        project = self._project_of(user)
        if project is None:
            return texts.GREETING_NO_PROJECT
        return texts.greeting_with_project(project.name)

    def _mentioned(self, text: str) -> Project | None:
        resolution = ProjectResolver.from_session(self.session).resolve(text)
        if not resolution.confident or resolution.best is None:
            return None
        return self.session.get(Project, resolution.best.project_id)

    def _adopt(self, user: WaUser, project: Project) -> bool:
        if user.project_id is not None:
            return False
        user.project_id = project.id
        self.session.flush()
        return True

    def _topic_reply(self, user: WaUser, text: str, intent: str | None) -> str | None:
        topic = intent if intent in EXACT_TOPICS else detect_topic(text)
        if topic is None:
            return None
        project = self._mentioned(text)
        adopted = False
        if project is None:
            project = self._project_of(user)
            if project is None:
                return texts.NEED_PROJECT if intent in EXACT_TOPICS else None
            if intent not in EXACT_TOPICS and not (
                refers_to_project(text) or is_short_topic(text, topic)
            ):
                return None
        else:
            adopted = self._adopt(user, project)
        self.turn_project_id = project.id
        reply = TOPIC_REPLIES[topic](self.session, project)
        return f"{reply} {texts.ADOPTED}" if adopted else reply

    def _register(self, user: WaUser, project_id: int) -> str:
        project = self.session.get(Project, project_id)
        if project is None:
            return texts.PROJECT_NOT_FOUND
        user.project_id = project.id
        self.turn_project_id = project.id
        self.session.flush()
        return self._registered_reply(project)

    def _registered_reply(self, project: Project) -> str:
        return f"{texts.project_registered(project.name)} {status_message(self.session, project)}"

    def _register_by_location(self, user: WaUser, latitude: float, longitude: float) -> str:
        project = ProjectRepository(self.session).locate(float(latitude), float(longitude))
        if project is None:
            return texts.LOCATION_OUTSIDE
        user.project_id = project.id
        self.turn_project_id = project.id
        self.session.flush()
        return self._registered_reply(project)

    def _respond(self, user: WaUser, message: IncomingMessage) -> None:
        phone = message.phone
        media_ok = self._granted(user, PURPOSE_MEDIA)
        if message.kind in {"image", "audio"} and not media_ok:
            self._reply(phone, texts.MEDIA_NOTICE)
            return
        if message.kind == "other":
            self._reply(phone, texts.UNSUPPORTED)
            return
        try:
            request = self._build_request(user, message, media_ok)
        except ExternalServiceError as exc:
            log.warning("media_unavailable", error=str(exc))
            self._reply(phone, texts.FAILURE)
            return
        if request is None:
            self._reply(phone, texts.AUDIO_UNCLEAR)
            return
        answer = self.agent.answer(request)
        self.turn_choices = answer.choices
        project = self.session.get(Project, answer.project_id) if answer.project_id else None
        adopted = False
        if project is not None:
            self.turn_project_id = project.id
            adopted = self._adopt(user, project)
        if answer.used_fallback and project is not None:
            reply = f"{texts.DEGRADED} {status_message(self.session, project)}"
        else:
            reply = answer.text
        self._reply(phone, f"{reply} {texts.ADOPTED}" if adopted else reply)
        if answer.used_fallback and not answer.evidence_ids:
            self._reply(phone, texts.HELP)

    def stage(self, phone: str) -> str:
        digest = phone_hmac(phone, self.settings.phone_hmac_key)
        user = self.session.scalars(select(WaUser).where(WaUser.phone_hmac == digest)).first()
        if user is None:
            return START
        if not self._granted(user, PURPOSE_DATA):
            return CONSENT
        return WITH_PROJECT if user.project_id else NO_PROJECT

    def turn_project(self) -> Project | None:
        return self.session.get(Project, self.turn_project_id) if self.turn_project_id else None

    def _build_request(
        self, user: WaUser, message: IncomingMessage, media_ok: bool
    ) -> AgentRequest | None:
        text = message.text or ""
        media: list[MediaPart] = []
        if message.kind == "audio" and message.media_id:
            data, mime = self.client.download_media(message.media_id)
            transcript = transcribe_audio(self.llm, MediaPart(data, mime))
            if transcript is None:
                return None
            text = transcript
        if message.kind == "image" and message.media_id:
            data, mime = self.client.download_media(message.media_id)
            media = [MediaPart(data, mime)]
            text = text or "Mire esta foto"
        project = self._project_of(user)
        return AgentRequest(
            text=text,
            role="comunidad",
            user_ref=user.phone_hmac,
            media=media,
            media_consent=media_ok,
            project=(project.id, project.name) if project else None,
        )
