// Toasts : notifications empilées en bas à droite, animées, auto-fermantes.
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";

type ToastKind = "success" | "error" | "info";
interface Toast { id: number; kind: ToastKind; message: string }

const ToastContext = createContext<{ toast: (kind: ToastKind, message: string) => void }>({
  toast: () => {},
});

const ICONS = { success: CheckCircle2, error: AlertTriangle, info: Info };
const COLORS = {
  success: "border-success/40 text-success",
  error: "border-danger/40 text-danger",
  info: "border-primary/40 text-primary",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);

  const toast = useCallback((kind: ToastKind, message: string) => {
    const id = nextId.current++;
    setToasts((current) => [...current, { id, kind, message }]);
    setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), 4200);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="pointer-events-none fixed bottom-5 right-5 z-[60] flex w-80 flex-col gap-2">
        <AnimatePresence>
          {toasts.map((t) => {
            const Icon = ICONS[t.kind];
            return (
              <motion.div
                key={t.id}
                layout
                initial={{ opacity: 0, x: 60 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 60 }}
                className={`glass pointer-events-auto flex items-start gap-2.5 rounded-xl border p-3.5 text-sm shadow-xl ${COLORS[t.kind]}`}
              >
                <Icon size={17} className="mt-0.5 shrink-0" />
                <span className="text-foreground">{t.message}</span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
