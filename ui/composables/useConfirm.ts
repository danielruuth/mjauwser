export function useConfirm() {
  const visible = ref(false)
  const title = ref('Confirm')
  const message = ref('')
  let resolveFn: ((value: boolean) => void) | null = null

  function ask(msg: string, ttl = 'Confirm'): Promise<boolean> {
    message.value = msg
    title.value = ttl
    visible.value = true
    return new Promise((resolve) => {
      resolveFn = resolve
    })
  }

  function onConfirm() {
    visible.value = false
    resolveFn?.(true)
    resolveFn = null
  }

  function onCancel() {
    visible.value = false
    resolveFn?.(false)
    resolveFn = null
  }

  return reactive({ visible, title, message, ask, onConfirm, onCancel })
}
