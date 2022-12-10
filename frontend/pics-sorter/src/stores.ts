import { writable } from 'svelte/store';
import axios from 'axios';

export const picsStore = writable({})

export async function getPics() {
  const response = await axios.get(`${window.location.origin}/api/pics/`);
  console.log(response.data)
  picsStore.set(response.data);
}
