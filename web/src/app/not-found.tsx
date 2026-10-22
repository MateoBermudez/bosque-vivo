import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md text-center">
        <p className="text-7xl font-extrabold text-primary">404</p>
        <h1 className="mt-4 text-xl font-semibold">Página no encontrada</h1>
        <p className="mt-2 text-sm text-muted-foreground">La página que buscas no existe o se movió.</p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <Link href="/" className="btn-dark">
            Volver al inicio
          </Link>
          <Link href="/proyectos" className="btn-outline">
            Ver proyectos
          </Link>
        </div>
      </div>
    </div>
  );
}
