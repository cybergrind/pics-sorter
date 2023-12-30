<script lang="ts">
  import { onMount } from 'svelte'
  import {
    picsStore,
    getPics,
    connectWS,
    setWinner as setWinnerStore,
    sendMsg,
    settings,
    toggleSetting
  } from '../stores'
  import { shortcut } from '../hotkeys'
  import { swipe, pinch } from 'svelte-gestures'
  //import Zoom from 'svelte-zoom'
  import Zoom from '../lib/zoom/index.svelte'
  import doubletap from '../lib/doubletap'

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
  let zoomMode = false
  const DEFAULT_ZOOM = 5

  $: navOnBottom = !!$settings.nav
  $: navClass = 'page-nav page-nav-' + (navOnBottom ? 'bottom' : 'top')

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
    resetZoom()
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
    resetZoom()
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
    if (zoomMode) {
      return
    }

    const { direction } = event.detail
    console.log('Direction:', direction)

    if (direction === 'bottom') {
      location.reload()
    } else if (direction === 'top') {
      single = undefined
      return
    }

    const zz = document.querySelector('#zoomed-img')
    if (zz && zz.style.transform !== 'matrix(1, 0, 0, 1, 0, 0)') {
      return
    }
    if (index === undefined) {
      index = pics.indexOf(single)
    }
    let inc = direction === 'left' ? 1 : 2
    index = (index + inc) % 3
    single = pics[index]
  }

  const resetZoom = () => {
    if (zoomMode) {
      zoomMode = false
    }
    const zz = document.querySelector('#zoomed-img')
    if (zz?.style.transform?.indexOf('scale(1)') === -1) {
      for (let i = 0; i < 10; i++) {
        zoom?.zoomOut()
      }
      return true
    }
    return false
  }

  const toggleOrZoomOut = () => {
    const zz = document.querySelector('#zoomed-img')
    if (!zz) {
      closeSingle()
    }
  }

  const toggleOrientation = async () => {
    await sendMsg({ event: 'toggle_orientation' })
    await getPics()
  }

  const addExtraCount = async () => {
    const extra_count = single.extra_count > 0 ? 1 : 2
    await sendMsg({ event: 'add_extra_count', image: single.path, count: extra_count })
    single.extra_count += extra_count
  }

  const onDoubletap = () => {
    console.log('doubletap click')
    zoomMode = !zoomMode
    if (zoomMode) {
      setTimeout(() => {
        for (let i = 0; i < DEFAULT_ZOOM; i++) {
          zoom?.zoomIn()
        }
      }, 30)
    }
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
      aria-hidden="true"
      use:swipe={{ timeframe: 300, minSwipeDistance: 80, touchAction: 'none' }}
      on:swipe={swipeHandler}
    >
      {#if zoomMode}
        <Zoom
          src={single.link}
          bind:this={zoom}
          on:load={() => console.log('on Load')}
          id="zoomed-img"
        />
      {:else}
        <img use:doubletap on:doubletap={onDoubletap} src={single.link} id="solo-img" />
      {/if}
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
  <div class={navClass}>
    {#if single}
        <button on:click|preventDefault={() => nextSingle()}>next</button>
        <button on:click={() => prevSingle()}>prev</button>
        <button on:click={() => setWinner(single)}>winner</button>
        <button on:click={() => addExtraCount(single)}>++</button>
        <button on:click={() => closeSingle()}>X</button>
        <span class="contrast">{single.elo_rating}/{single.extra_count}</span>
        <button on:click={() => toggleSetting('nav')}>MM</button>
      {#if zoomMode}
        <button on:click={() => resetZoom()}>RST</button>
      {/if}
    {:else}
      <button on:click={toggleOrientation}>
        {#if $settings.same_orientation}
          Orientation {$settings.same_orientation}
        {:else}
          No Orientation
        {/if}
      </button>
      <span>{w}x{h} => {orientation}</span>
      <span class="contrast">
        {#each pics as image} |{image.elo_rating}/{image.extra_count} {/each}</span
      >
      <button on:click={() => sendMsg({ event: 'build_top10' })}>Build Top10</button>
      <button on:click={() => sendMsg({ event: 'touch_restart' })}>Reindex</button>
      <button on:click={() => toggleSetting('nav')}>Move nav</button>
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

  .page-nav {
    position: fixed;
    left: 0;
    width: 100%;
    z-index: 999;
  }
  .page-nav-bottom {
    bottom: 0;
  }
  .page-nav > button {
    height: 3.5vh;
    margin-right: 10px;
  }

  .container {
    flex: 1 0 auto;
    display: flex;
    flex-flow: row wrap;
    padding: 0;
    max-height: 100vh;
    max-width: 100vw;
  }

  .img-fit {
    max-width: 33%;
    max-height: 32%;
  }
  .img-fit > img {
    max-width: 33vw;
    max-height: 97vh;
  }
  #solo-img {
    max-width: 100vw;
    max-height: 100vh;
    margin: auto;
    object-fit: contain;
    width: 100%;
  }

  .contrast {
    color: black;
    background-color: white;
  }
</style>
