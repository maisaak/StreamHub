import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number | null | undefined): string {
  if (price == null) return "";
  return `${Math.round(price)} ₽`;
}

export function accessLabel(s: { is_subscription: boolean; price: number | null }): string {
  if (s.is_subscription) return "подписка";
  if (s.price != null) return "аренда";
  return "бесплатно";
}
