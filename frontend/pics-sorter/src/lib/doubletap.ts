import { setPointerControls, DEFAULT_DELAY } from 'svelte-gestures'

const gestureName = 'doubletap'
const spread = 20

export default function doubletap(node, parameters = { timeframe: DEFAULT_DELAY }) {
  let startTime
  let clientX
  let clientY
  let tapCount = 0
  let timeout

  function onUp(activeEvents, event) {
    if (
      Math.abs(event.clientX - clientX) < spread &&
      Math.abs(event.clientY - clientY) < spread &&
      Date.now() - startTime < parameters.timeframe
    ) {
      if (!tapCount) {
        tapCount++
      } else {
        const rect = node.getBoundingClientRect()
        const x = Math.round(event.clientX - rect.left)
        const y = Math.round(event.clientY - rect.top)

        node.dispatchEvent(
          new CustomEvent(gestureName, {
            detail: { x, y }
          })
        )

        clearTimeout(timeout)
        tapCount = 0
      }
    }
  }

  function onDown(activeEvents, event) {
    if (!tapCount) {
      clientX = event.clientX
      clientY = event.clientY
      startTime = Date.now()
    }

    timeout = setTimeout(() => {
      tapCount = 0
    }, parameters.timeframe)
  }

  return setPointerControls(gestureName, node, null, onDown, onUp)
}
