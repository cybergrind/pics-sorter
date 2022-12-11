<script lang="ts">
  import { onMount } from 'svelte';
  import { picsStore, getPics } from '../stores.ts'
  import { shortcut } from '../hotkeys.ts'
  import { swipe, pinch } from 'svelte-gestures';
  import Zoom from 'svelte-zoom'

  onMount(async () => {
    await getPics()
  })

  let pics, single, index
  let zoom;
  picsStore.subscribe(value => pics = value)

  const swipeHandler = async (event) => {
    const { direction } = event.detail;
    console.log('Direction:', direction)

    if (direction === 'bottom') {
      location.reload()
    } else if (direction === 'top') {
      single = undefined
      return
    } else if (direction !== 'left') {
      return true;
    }
    const zz = document.querySelector('#zoomed-img')
    if (zz.style.transform !== 'matrix(1, 0, 0, 1, 0, 0)'){
      return
    }
    if (index === undefined) {
       index = pics.images.indexOf(single)
    }
    if (index >= 2) {
       await getPics();
       index = -1
    }
    index += 1
    single = pics.images[index]
  }

  const pinchHandler = (event) => {
     zoom = Math.min(zoom * event.detail.scale, 1)
  }

  const toggleOrZoomOut = () => {
    const zz = document.querySelector('#zoomed-img')
    if (zz && zz.style.transform && zz.style.transform.indexOf('scale(1)') === -1) {
      for (let i = 0; i < 10; i++) {
        zoom.zoomOut()
      }
    } else {
      single = undefined
    }
  }
  
</script>

{#if single }
    <div
      use:shortcut={{code: 'Space', callback: async () => single = undefined}}
      use:shortcut={{code: 'KeyF', callback: () => single = undefined }}
      use:shortcut={{code: 'KeyD', callback: () => single = undefined }}
      use:shortcut={{code: 'KeyS', callback: () => single = undefined }}
      use:swipe={{ timeframe: 300, minSwipeDistance: 80 }}
      on:click={toggleOrZoomOut}
      on:swipe={swipeHandler}
     >
    <Zoom src={single} bind:this={zoom} on:load={() => console.log('on Load')}
      id="zoomed-img"/>
   </div>
{:else if pics.images && pics.images.length > 0}
    <div class="container"
        use:shortcut={{code: 'Space', callback: async () => getPics() }}
        use:shortcut={{code: 'KeyF', callback: () => single = pics.images[2] }}
        use:shortcut={{code: 'KeyD', callback: () => single = pics.images[1] }}
        use:shortcut={{code: 'KeyS', callback: () => single = pics.images[0] }}
    >
    {#each pics.images as image}
        <img src={image} class="img-fit"
             alt="some picture"
             on:click={() => {
           console.log('Image:', image)
           single=image
        }} />
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
    .full-div {
    }
    .img-full {
        height: 100vh;
        width: auto;
        margin-left: auto;
        margin-right: auto;
        display: block;
    }
    .img-zoomed {
    }
    .img-fit {
        max-width: 33%;
        max-height: 33%;
    }
</style>
