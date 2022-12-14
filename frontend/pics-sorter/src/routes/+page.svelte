<script lang="ts">
	import { onMount } from 'svelte'
	import { picsStore, getPics, connectWS, setWinner, sendMsg, sameOrientation } from '../stores'
	import { shortcut } from '../hotkeys'
	import { swipe, pinch } from 'svelte-gestures'
	import Zoom from 'svelte-zoom'

	import type { Image } from '../types'

	onMount(async () => {
		await getPics()
		connectWS()
	})

	let pics: Image[], single: Image | undefined, index: number | undefined
	let zoom: Zoom | undefined

	picsStore.subscribe((value: Image[]) => {
		pics = value
		if (single) {
			index = 0
			single = pics[index]
		}
	})

	const nextSingle = () => {
		if (single === undefined) {
			single = pics[0]
		}
		if (index === undefined) {
			index = pics.indexOf(single)
		}
		index = (index + 1) % pics.length
		single = pics[index]
	}

	const prevSingle = () => {
		if (single === undefined) {
			single = pics[pics.length - 1]
		}
		if (index === undefined) {
			index = pics.indexOf(single)
		}
		index = (index - 1 + pics.length) % pics.length
		single = pics[index]
	}

	const closeSingle = () => {
		single = undefined
		index = undefined
	}

	const swipeHandler = async (event) => {
		const { direction } = event.detail
		console.log('Direction:', direction)

		if (direction === 'bottom') {
			location.reload()
		} else if (direction === 'top') {
			single = undefined
			return
		} else if (direction !== 'left') {
			return true
		}
		const zz = document.querySelector('#zoomed-img')
		if (zz?.style.transform !== 'matrix(1, 0, 0, 1, 0, 0)') {
			return
		}
		if (index === undefined) {
			index = pics.indexOf(single)
		}
		if (index >= 2) {
			await getPics()
			index = -1
		}
		index += 1
		single = pics[index]
	}

	const toggleOrZoomOut = () => {
		const zz = document.querySelector('#zoomed-img')
		if (zz && zz.style.transform && zz.style.transform.indexOf('scale(1)') === -1) {
			for (let i = 0; i < 10; i++) {
				zoom?.zoomOut()
			}
		} else {
			closeSingle()
		}
	}
	const toggleOrientation = async () => {
		await sendMsg({ event: 'toggle_orientation' })
		await getPics()
	}
</script>

{#if single}
	<div
		use:shortcut={{ code: 'Space', callback: async () => closeSingle() }}
		use:shortcut={{ code: 'KeyF', callback: () => closeSingle() }}
		use:shortcut={{ code: 'KeyD', callback: () => closeSingle() }}
		use:shortcut={{ code: 'KeyS', callback: () => closeSingle() }}
		use:shortcut={{
			code: 'KeyG',
			callback: () => {
				if (single === undefined) {
					return
				}
				setWinner(single)
				nextSingle()
			}
		}}
		use:shortcut={{
			code: 'KeyA',
			callback: () => {
				nextSingle()
			}
		}}
		use:shortcut={{
			code: 'KeyZ',
			callback: () => {
				prevSingle()
			}
		}}
		use:shortcut={{
			code: 'Digit6',
			callback: async () => {
				sendMsg({ event: 'hide', image: single?.path })
				await getPics()
			}
		}}
		use:swipe={{ timeframe: 300, minSwipeDistance: 80, touchAction: 'none' }}
		on:click={toggleOrZoomOut}
		aria-hidden="true"
		on:swipe={swipeHandler}
	>
		<Zoom
			src={single.link}
			bind:this={zoom}
			on:load={() => console.log('on Load')}
			id="zoomed-img"
		/>
	</div>
{:else if pics && pics.length > 0}
	<button on:click={toggleOrientation}>
		{#if $sameOrientation}
			Orientation {$sameOrientation}
		{:else}
			No Orientation
		{/if}
	</button>
	<div
		class="container"
		use:shortcut={{ code: 'Space', callback: async () => getPics() }}
		use:shortcut={{ code: 'KeyR', callback: () => setWinner(pics[2]) }}
		use:shortcut={{ code: 'KeyE', callback: () => setWinner(pics[1]) }}
		use:shortcut={{ code: 'KeyW', callback: () => setWinner(pics[0]) }}
		use:shortcut={{ code: 'KeyF', callback: () => (single = pics[2]) }}
		use:shortcut={{ code: 'KeyD', callback: () => (single = pics[1]) }}
		use:shortcut={{ code: 'KeyS', callback: () => (single = pics[0]) }}
		use:shortcut={{ code: 'KeyA', callback: () => (single = pics[0]) }}
	>
		{#each pics as image}
			<div class="img-fit">
				<!--><button on:click={() => setWinner(image)}>win</button><-->

				<img
					src={image.link}
					alt="some picture"
					aria-hidden="true"
					on:click={() => {
						console.log('Image:', image)
						single = image
					}}
				/>
			</div>
		{/each}
	</div>
{:else}
	<p>loading...</p>
{/if}

<style>
	.container {
		display: flex;
		flex-wrap: wrap;
		flex-flow: row wrap;
		align-items: center;
		padding: 0;
	}
	.img-fit {
		max-width: 33%;
		max-height: 32%;
	}
	.img-fit > img {
		max-width: 33vw;
		max-height: 97vh;
	}
</style>
