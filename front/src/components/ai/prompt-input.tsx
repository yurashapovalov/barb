import { CornerDownLeftIcon } from "lucide-react"
import {
  type ComponentProps,
  createContext,
  type HTMLAttributes,
  type KeyboardEventHandler,
  useContext,
  useState,
} from "react"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group"
import { cn } from "@/lib/utils"

// ============================================================================
// Provider
// ============================================================================

interface TextInputContext {
  value: string
  setInput: (v: string) => void
  clear: () => void
}

interface ControllerContext {
  textInput: TextInputContext
}

const ControllerCtx = createContext<ControllerContext | null>(null)

export function usePromptInputController() {
  const ctx = useContext(ControllerCtx)
  if (!ctx) {
    throw new Error("Wrap your component inside <PromptInputProvider>.")
  }
  return ctx
}

export function PromptInputProvider({ children }: { children: React.ReactNode }) {
  const [value, setValue] = useState("")

  const controller: ControllerContext = {
    textInput: {
      value,
      setInput: setValue,
      clear: () => setValue(""),
    },
  }

  return <ControllerCtx.Provider value={controller}>{children}</ControllerCtx.Provider>
}

// ============================================================================
// PromptInput (form)
// ============================================================================

export type PromptInputProps = Omit<HTMLAttributes<HTMLFormElement>, "onSubmit"> & {
  onSubmit: (message: { text: string }) => void | Promise<void>
}

export const PromptInput = ({ className, onSubmit, children, ...props }: PromptInputProps) => {
  const controller = useContext(ControllerCtx)

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const text = controller
      ? controller.textInput.value
      : new FormData(event.currentTarget).get("message") as string || ""

    if (!controller) {
      event.currentTarget.reset()
    }

    const result = onSubmit({ text })

    if (result instanceof Promise) {
      result
        .then(() => controller?.textInput.clear())
        .catch((err) => console.error("Failed to send message:", err))
    } else {
      controller?.textInput.clear()
    }
  }

  return (
    <form className={cn("w-full", className)} onSubmit={handleSubmit} {...props}>
      <InputGroup className="overflow-hidden">{children}</InputGroup>
    </form>
  )
}

// ============================================================================
// Sub-components
// ============================================================================

export type PromptInputBodyProps = HTMLAttributes<HTMLDivElement>

export const PromptInputBody = ({ className, ...props }: PromptInputBodyProps) => (
  <div className={cn("contents", className)} {...props} />
)

export type PromptInputTextareaProps = ComponentProps<typeof InputGroupTextarea>

export const PromptInputTextarea = ({
  onChange,
  className,
  placeholder = "What would you like to know?",
  ...props
}: PromptInputTextareaProps) => {
  const controller = useContext(ControllerCtx)
  const [isComposing, setIsComposing] = useState(false)

  const handleKeyDown: KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === "Enter") {
      if (isComposing || e.nativeEvent.isComposing || e.shiftKey) return
      e.preventDefault()

      const form = e.currentTarget.form
      const submitBtn = form?.querySelector('button[type="submit"]') as HTMLButtonElement | null
      if (submitBtn?.disabled) return

      form?.requestSubmit()
    }
  }

  const controlledProps = controller
    ? {
        value: controller.textInput.value,
        onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => {
          controller.textInput.setInput(e.currentTarget.value)
          onChange?.(e)
        },
      }
    : { onChange }

  return (
    <InputGroupTextarea
      className={cn("field-sizing-content max-h-48", className)}
      name="message"
      onCompositionEnd={() => setIsComposing(false)}
      onCompositionStart={() => setIsComposing(true)}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      {...props}
      {...controlledProps}
    />
  )
}

export type PromptInputFooterProps = Omit<ComponentProps<typeof InputGroupAddon>, "align">

export const PromptInputFooter = ({ className, ...props }: PromptInputFooterProps) => (
  <InputGroupAddon align="block-end" className={cn("justify-between gap-1", className)} {...props} />
)

export type PromptInputSubmitProps = ComponentProps<typeof InputGroupButton>

export const PromptInputSubmit = ({
  className,
  variant = "default",
  size = "icon-sm",
  children,
  ...props
}: PromptInputSubmitProps) => (
  <InputGroupButton
    aria-label="Submit"
    className={cn(className)}
    size={size}
    type="submit"
    variant={variant}
    {...props}
  >
    {children ?? <CornerDownLeftIcon className="size-4" />}
  </InputGroupButton>
)
