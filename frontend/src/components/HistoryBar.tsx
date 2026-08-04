import type { MonitorHistoryItem } from "@/api/client";
import { statusBarColor } from "@/components/StatusBadge";
import { cn } from "@/lib/utils";

const MAX_VISIBLE_CHECKS = 36;

export function HistoryBar({
  history,
  onSelect,
}: {
  history: MonitorHistoryItem[];
  onSelect: (check: MonitorHistoryItem) => void;
}) {
  const visibleHistory = history.slice(-MAX_VISIBLE_CHECKS);
  const emptySlots = Math.max(0, MAX_VISIBLE_CHECKS - visibleHistory.length);
  const slots = [
    ...Array.from({ length: emptySlots }, () => null),
    ...visibleHistory,
  ];

  return (
    <div
      className="flex h-4 w-full items-stretch gap-px overflow-hidden rounded-md"
      role="img"
      aria-label={`Últimas ${visibleHistory.length} de ${history.length} checagens`}
      title={
        history.length
          ? `Exibindo as últimas ${visibleHistory.length} de ${history.length} checagens`
          : "Sem histórico"
      }
    >
      {slots.map((check, i) =>
        check ? (
          <button
            key={check.id}
            type="button"
            className={cn(
              "min-w-[2px] flex-1 cursor-pointer transition-transform hover:scale-y-125 focus-visible:z-10 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white/70",
              statusBarColor(check.result),
            )}
            title={`Ver resposta de ${new Date(check.checked_at).toLocaleString("pt-BR")}`}
            aria-label={`Ver resposta da checagem ${i + 1}`}
            onClick={() => onSelect(check)}
          />
        ) : (
          <div key={`empty-${i}`} className="min-w-[2px] flex-1 bg-zinc-800" />
        ),
      )}
    </div>
  );
}
