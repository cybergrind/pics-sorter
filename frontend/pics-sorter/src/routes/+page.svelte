<script lang="ts">
	import { onMount } from 'svelte'
	import { picsStore, getPics, connectWS, setWinner as setWinnerStore, sendMsg, sameOrientation } from '../stores'
	import { shortcut } from '../hotkeys'
	import { swipe, pinch } from 'svelte-gestures'
	import Zoom from 'svelte-zoom'

	import type { Image } from '../types'

	onMount(async () => {
		await getPics()
		connectWS()
	})

	let w, h
	let pics: Image[]
	let single: Image | undefined
	let index: number | undefined
	let zoom: Zoom | undefined

	const setSingle = (pic: Image) => {
		index = pics.indexOf(pic)
		single = pics[index]
	}

	picsStore.subscribe((value: Image[]) => {
		pics = value
		if (single) {
			single = pics[index]
		}
	})

  const setWinner = (pic: Image) => {
    index = 0
    setWinnerStore(pic)
    console.log('SetWinner: ', pic, index)
  }

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

	const resetZoom = () => {
		const zz = document.querySelector('#zoomed-img')
		if (zz && zz.style.transform && zz.style.transform.indexOf('scale(1)') === -1) {
			for (let i = 0; i < 10; i++) {
				zoom?.zoomOut()
			}
			return true
		}
		return false
	}

	const toggleOrZoomOut = () => {
		const zz = document.querySelector('#zoomed-img')
		if (!resetRoom) {
			closeSingle()
		}
	}

	const toggleOrientation = async () => {
		await sendMsg({ event: 'toggle_orientation' })
		await getPics()
	}

  const addExtraCount = async () => {
    const extra_count = single.extra_count > 0 ? 1 : 2
    await sendMsg({ event: 'add_extra_count', 'image': single.path, 'count': extra_count})
    single.extra_count += extra_count
  }

	$: orientation = w > h ? 'landscape' : 'portrait'
</script>

<div class="app">
	{#if single}
		<div
			class="container"
			use:shortcut={{ code: 'Space', callback: async () => closeSingle() }}
			use:shortcut={{ code: 'KeyF', callback: () => closeSingle() }}
			use:shortcut={{ code: 'KeyD', callback: () => closeSingle() }}
			use:shortcut={{ code: 'KeyS', callback: () => closeSingle() }}
      use:shortcut={{ code: 'KeyB', callback: () => addExtraCount() }}
			use:shortcut={{
				code: 'KeyG',
				callback: () => {
					if (single === undefined) {
						return
					}
					setWinner(single)
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
				}
			}}
      use:shortcut={{
				code: 'Digit5',
				callback: async () => {
					sendMsg({ event: 'restore_last' })
				}
			}}
			on:click={toggleOrZoomOut}
			aria-hidden="true"
			use:swipe={{ timeframe: 300, minSwipeDistance: 80, touchAction: 'none' }}
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
		<div
			class="container"
			use:shortcut={{ code: 'Space', callback: async () => getPics() }}
			use:shortcut={{ code: 'KeyR', callback: () => setWinner(pics[2]) }}
			use:shortcut={{ code: 'KeyE', callback: () => setWinner(pics[1]) }}
			use:shortcut={{ code: 'KeyW', callback: () => setWinner(pics[0]) }}
			use:shortcut={{ code: 'KeyF', callback: () => setSingle(pics[2]) }}
			use:shortcut={{ code: 'KeyD', callback: () => setSingle(pics[1]) }}
			use:shortcut={{ code: 'KeyS', callback: () => setSingle(pics[0]) }}
			use:shortcut={{ code: 'KeyA', callback: () => setSingle(pics[0]) }}
      use:shortcut={{
				code: 'Digit5',
				callback: async () => {
					sendMsg({ event: 'restore_last' })
				}
			}}
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
	<div class="bottom-nav">
		{#if single}
			<button on:click|preventDefault={() => nextSingle()}>next</button>
			<button on:click={() => prevSingle()}>prev</button>

			<button on:click={() => setWinner(single)}>winner</button>
      <button on:click={() => addExtraCount(single)}>++</button>
			<button on:click={() => closeSingle()}>X</button>
      <span>{single.elo_rating}/{single.extra_count}</span>
		{:else}
			<button on:click={toggleOrientation}>
				{#if $sameOrientation}
					Orientation {$sameOrientation}
				{:else}
					No Orientation
				{/if}
			</button>
			<span>{w}x{h} => {orientation}</span>
      <span> {#each pics as image} |{image.elo_rating}/{image.extra_count} {/each}</span>
      <button on:click={() => sendMsg({event: 'build_top10'})}>Build Top10</button>
		{/if}
	</div>
</div>
<svelte:window bind:innerWidth={w} bind:innerHeight={h} />

<style>
	.app {
		display: grid;
		grid-template-rows: 1fr auto;
		min-height: 100%;
	}

	.bottom-nav {
		z-index: 2;
		rid-row-start: 2;
		grid-row-end: 3;
	}
	.bottom-nav > button {
		height: 45px;
		margin-right: 20px;
	}

	.container {
		flex: 1 0 auto;
		display: flex;
		flex-flow: row wrap;
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
