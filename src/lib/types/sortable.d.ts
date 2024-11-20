declare module 'sortablejs' {
	interface SortableOptions {
		animation?: number;
		onUpdate?: (event: SortableEvent) => void;
	}
	interface SortableEvent {
		oldIndex: number;
		newIndex: number;
	}

	class Sortable {
		constructor(element: Element | null, options?: SortableOptions);
	}

	export = Sortable;
}
