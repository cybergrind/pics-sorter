import { writable } from 'svelte/store'
import axios from 'axios'
import ReconnectingWebSocket from 'reconnecting-websocket'

export const picsStore = writable({})
export const sameOrientation = writable(0)

let _pics
picsStore.subscribe((value) => {
	_pics = value
})

export async function getPics() {
	const response = await axios.get(`${window.location.origin}/api/pics/`)
	console.log(response.data)
	picsStore.set(response.data.images)
	sameOrientation.set(response.data.same_orientation)
}

const MAX_EVENTS = 10

export const events = writable([])
// add in front and limit to 10
export const addEvent = (event) => {
	events.update((events) => {
		events.unshift(event)
		return events.slice(0, MAX_EVENTS)
	})
	console.log('Event: ', event)

	if (event.event === 'rate_success') {
		getPics()
	}
}

let _ws

export const connectWS = () => {
	if (_ws !== undefined) return

	events.subscribe((evts) => (window.evts = evts))
	_ws = new ReconnectingWebSocket(`ws://${window.location.host}/ws`)
	_ws.addEventListener('message', (event) => {
		addEvent(JSON.parse(event.data))
	})
}

export const setWinner = (winner) => {
	const loosersObjs = _pics.filter((pic) => pic.path !== winner.path)
	const loosers = loosersObjs.map((v) => v.path)
	_ws.send(JSON.stringify({ event: 'rate', winner: winner.path, loosers }))
}

export const sendMsg = (msg) => {
	_ws.send(JSON.stringify(msg))
}
