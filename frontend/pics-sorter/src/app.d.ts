// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
// and what to do when importing types
declare namespace App {
	// interface Error {}
	// interface Locals {}
	// interface PageData {}
	// interface Platform {}
}

interface Element {
    style: CSSStyleDeclaration
}

interface Zoom {
	zoomIn: () => void
	zoomOut: () => void
}