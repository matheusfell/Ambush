import {
  forwardRef,
  useEffect,
  useId,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type KeyboardEvent as ReactKeyboardEvent,
  type ReactNode,
  type TextareaHTMLAttributes,
} from "react";
import { Check, ChevronDown, X } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  BUTTON_BASE,
  BUTTON_PRIMARY,
  CONTROL_OUTLINE,
  CONTROL_SURFACE,
  ICON_BUTTON,
  PANEL,
} from "@/components/controlStyles";

export function Panel({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={cn(PANEL, className)}>{children}</div>;
}

export function Card({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={cn(PANEL, "p-4", className)}>{children}</div>;
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "primary" | "danger";
};

export function Button({
  className,
  variant = "default",
  type = "button",
  ...props
}: ButtonProps) {
  const variantClass =
    variant === "primary"
      ? BUTTON_PRIMARY
      : variant === "danger"
        ? "inline-flex h-9 items-center justify-center gap-2 rounded-lg border border-red-900 bg-red-950/40 px-3 text-sm font-medium text-red-400 hover:bg-red-950/70 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/50"
        : BUTTON_BASE;
  return <button type={type} className={cn(variantClass, className)} {...props} />;
}

export function IconButton({
  className,
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type={type} className={cn(ICON_BUTTON, CONTROL_OUTLINE, className)} {...props} />;
}

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  function Input({ className, type = "text", ...props }, ref) {
    return (
      <input
        ref={ref}
        type={type}
        className={cn(
          CONTROL_SURFACE,
          CONTROL_OUTLINE,
          "w-full",
          type === "number" && "theme-number",
          className,
        )}
        {...props}
      />
    );
  },
);

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      className={cn(
        "min-h-20 w-full rounded-lg border border-zinc-700 bg-[#1c1c1f] px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600",
        CONTROL_OUTLINE,
        className,
      )}
      {...props}
    />
  );
});

export type ListboxOption<T extends string> = {
  value: T;
  label: string;
};

export function Listbox<T extends string>({
  id,
  value,
  options,
  onChange,
  className,
  "aria-label": ariaLabel,
}: {
  id?: string;
  value: T;
  options: ListboxOption<T>[];
  onChange: (value: T) => void;
  className?: string;
  "aria-label"?: string;
}) {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const selected = options.find((option) => option.value === value) ?? options[0];
  const listboxId = useId();

  function select(next: T) {
    onChange(next);
    setOpen(false);
    buttonRef.current?.focus();
  }

  function onKeyDown(event: ReactKeyboardEvent<HTMLButtonElement>) {
    const index = Math.max(
      0,
      options.findIndex((option) => option.value === value),
    );

    if (event.key === "Escape") {
      setOpen(false);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setOpen((current) => !current);
      return;
    }

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      const nextIndex = (index + direction + options.length) % options.length;
      onChange(options[nextIndex].value);
      setOpen(true);
    }
  }

  return (
    <div className={cn("relative", className)}>
      <button
        ref={buttonRef}
        id={id}
        type="button"
        role="combobox"
        aria-label={ariaLabel}
        aria-controls={listboxId}
        aria-expanded={open}
        aria-haspopup="listbox"
        className={cn(
          "flex h-9 w-full items-center justify-between rounded-lg border border-zinc-700 bg-[#1c1c1f] px-3 text-left text-sm text-zinc-100 hover:border-zinc-600",
          CONTROL_OUTLINE,
        )}
        onClick={() => setOpen((current) => !current)}
        onKeyDown={onKeyDown}
      >
        <span>{selected.label}</span>
        <ChevronDown className="size-4 text-zinc-500" aria-hidden />
      </button>

      {open && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 cursor-default"
            aria-label="Fechar lista"
            tabIndex={-1}
            onClick={() => setOpen(false)}
          />
          <div
            id={listboxId}
            role="listbox"
            className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border border-zinc-700 bg-[#1c1c1f] p-1 shadow-xl"
          >
            {options.map((option) => {
              const active = option.value === value;
              return (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={active}
                  className={cn(
                    "flex h-8 w-full items-center justify-between rounded-md px-2 text-left text-sm",
                    active
                      ? "bg-zinc-800 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100",
                  )}
                  onClick={() => select(option.value)}
                >
                  <span>{option.label}</span>
                  {active && <Check className="size-3.5 text-emerald-400" aria-hidden />}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

type CheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: ReactNode;
};

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  function Checkbox({ className, label, id, disabled, ...props }, ref) {
    const autoId = useId();
    const inputId = id ?? autoId;

    return (
      <label
        htmlFor={inputId}
        className={cn(
          "inline-flex cursor-pointer items-center gap-2.5 text-sm text-zinc-300 select-none",
          disabled && "cursor-not-allowed opacity-50",
          className,
        )}
      >
        <span className="relative inline-flex size-4 shrink-0">
          <input
            ref={ref}
            id={inputId}
            type="checkbox"
            disabled={disabled}
            className="peer sr-only"
            {...props}
          />
          <span
            aria-hidden
            className={cn(
              "flex size-4 items-center justify-center rounded-[5px] border border-zinc-600 bg-[#1c1c1f] transition-colors",
              "peer-hover:border-zinc-500",
              "peer-focus-visible:ring-1 peer-focus-visible:ring-white/50",
              "peer-checked:border-emerald-700 peer-checked:bg-emerald-950 peer-checked:[&_svg]:opacity-100",
              "peer-aria-[invalid=true]:border-red-700",
            )}
          >
            <Check
              className="size-3 text-emerald-400 opacity-0 transition-opacity"
              strokeWidth={3}
              aria-hidden
            />
          </span>
        </span>
        <span>{label}</span>
      </label>
    );
  },
);

export function Label({
  children,
  htmlFor,
  className,
}: {
  children: ReactNode;
  htmlFor?: string;
  className?: string;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className={cn("mb-1.5 block text-xs font-medium text-zinc-400", className)}
    >
      {children}
    </label>
  );
}

export function FieldError({ children }: { children?: ReactNode }) {
  if (!children) return null;
  return <p className="mt-1 text-xs text-red-400">{children}</p>;
}

export function StatusBadge({
  tone,
  children,
  className,
}: {
  tone: "emerald" | "amber" | "red" | "sky" | "zinc";
  children: ReactNode;
  className?: string;
}) {
  const tones: Record<string, string> = {
    emerald: "border-emerald-900 bg-emerald-950/50 text-emerald-400",
    amber: "border-amber-900 bg-amber-950/40 text-amber-400",
    red: "border-red-900 bg-red-950/40 text-red-400",
    sky: "border-sky-900 bg-sky-950/40 text-sky-400",
    zinc: "border-zinc-700 bg-zinc-900 text-zinc-400",
  };
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center gap-1.5 whitespace-nowrap rounded-full border px-2 text-xs font-medium",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-lg bg-zinc-800/80", className)} />;
}

export function Modal({
  open,
  title,
  onClose,
  children,
  footer,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/70"
        aria-label="Fechar diálogo"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative z-10 flex max-h-[90vh] w-full max-w-lg flex-col rounded-xl border border-zinc-800 bg-[#161618] shadow-2xl"
      >
        <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
          <h2 className="text-sm font-semibold text-zinc-100">{title}</h2>
          <IconButton aria-label="Fechar" onClick={onClose}>
            <X className="size-4" />
          </IconButton>
        </div>
        <div className="overflow-y-auto px-4 py-4">{children}</div>
        {footer && (
          <div className="flex justify-end gap-2 border-t border-zinc-800 px-4 py-3">{footer}</div>
        )}
      </div>
    </div>
  );
}
