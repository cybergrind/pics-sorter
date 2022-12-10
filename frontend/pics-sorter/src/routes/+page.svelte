<script lang="ts">
  import { onMount } from 'svelte';
  import { picsStore, getPics } from '../stores.ts'
  import { shortcut } from '../hotkeys.ts'

  onMount(async () => {
    await getPics()
  })

  let pics, single
  picsStore.subscribe(value => pics = value)
  
</script>

{#if single }
    <div use:shortcut={{code: 'Space', callback: async () => {
        single = undefined
        await getPics()
        }
     }}>
       <img src={single} class="img-full">
   </div>
{:else if pics.images && pics.images.length > 0}
    <div class="container"
        use:shortcut={{code: 'Space', callback: async () => getPics() }}
        use:shortcut={{code: 'KeyF', callback: () => single = pics.images[2] }}
        use:shortcut={{code: 'KeyD', callback: () => single = pics.images[1] }}
        use:shortcut={{code: 'KeyS', callback: () => single = pics.images[0] }}
    >
    {#each pics.images as image}
       <img src={image} class="img-fit"/>
    {/each}
  </div>
{:else}
  <p>loading...</p>
{/if}

<style>
    body {
        margin: 0;
    }
    .container {
        display: flex;
        flex-wrap: wrap;
        flex-flow: row wrap;
        align-items: center;
        padding: 0;
    }
    .img-full {
        max-width: auto;
        max-height: 100vh;
    }
    .img-fit {
        max-width: 33%;
        max-height: 33%;
    }
</style>
