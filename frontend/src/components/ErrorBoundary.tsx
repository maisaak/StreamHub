import { Component, type ReactNode } from "react";
import { Link } from "react-router-dom";

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (this.state.failed) {
      return (
        <div className="mx-auto max-w-lg p-8 text-center">
          <h1 className="text-xl font-bold">Что-то пошло не так</h1>
          <p className="mt-2 text-sm text-neutral-500">
            Мы уже чиним. Попробуйте обновить страницу.
          </p>
          <div className="mt-4 flex justify-center gap-2">
            <button
              onClick={() => window.location.reload()}
              className="rounded-xl bg-brand-500 px-4 py-2 text-sm font-semibold text-white"
            >
              Обновить
            </button>
            <Link to="/" className="rounded-xl border px-4 py-2 text-sm font-semibold">
              На главную
            </Link>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
