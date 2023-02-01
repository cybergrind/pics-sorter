export interface Image {
	path: string
	link: string
  id: number,
  elo_rating: number,
  extra_count: number,
}

export type ImageList = Image[]
