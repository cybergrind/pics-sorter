import { writable, type Writable } from 'svelte/store'
import axios from 'axios'
import ReconnectingWebSocket from 'reconnecting-websocket'
import type { Image } from './types'

export const picsStore: Writable<Image[]> = writable([])

let _pics: Image[]
picsStore.subscribe((value) => {
  _pics = value
})

export const settings: Writable<Record<string, any>> = writable({})

export async function getPics(is_random = false) {
  const response = await axios.get(`${window.location.origin}/api/pics/`, {params: {is_random}})
  console.log(response.data)
  picsStore.set(response.data.images)
  settings.set(response.data.settings)
}

const MAX_EVENTS = 10

export const events = writable([])
// add in front and limit to 10

const GET_PICS_EVENTS = ['rate_success', 'hide_success', 'restore_success']
export const addEvent = (event) => {
  events.update((events) => {
    events.unshift(event)
    return events.slice(0, MAX_EVENTS)
  })
  console.log('Event: ', event)

  if (GET_PICS_EVENTS.includes(event.event)) {
    getPics(event.is_random)
  }
  switch (event.event) {
    case 'update_settings':
      settings.update(() => event.settings)
      break
    default:
      break
  }
}

let _ws: ReconnectingWebSocket

export const connectWS = () => {
  if (_ws !== undefined) return

  events.subscribe((evts) => (window.evts = evts))
  _ws = new ReconnectingWebSocket(`ws://${window.location.host}/ws`)
  _ws.addEventListener('message', (event) => {
    addEvent(JSON.parse(event.data))
  })
}

export const setWinner = (winner: Image, isRandom: false) => {
  const loosersObjs = _pics.filter((pic) => pic.path !== winner.path)
  const loosers = loosersObjs.map((v) => v.path)
  _ws.send(JSON.stringify({ event: 'rate', winner: winner.path, loosers, is_random: isRandom }))
}

export const toggleSetting = (name: string) => {
  _ws.send(JSON.stringify({ event: 'toggle_setting', name: name }))
}

export const sendMsg = (msg: { event: string }) => {
  _ws.send(JSON.stringify(msg))
}
