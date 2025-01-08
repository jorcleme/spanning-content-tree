import type { ComponentProps, SvelteComponent } from 'svelte';
import { $applyNodeReplacement, DecoratorNode, createEditor } from 'lexical';
import type {
	DOMConversionMap,
	DOMExportOutput,
	EditorConfig,
	LexicalEditor,
	LexicalNode,
	NodeKey,
	SerializedEditor,
	SerializedLexicalNode,
	Spread
} from 'lexical';
import ImageComponent from './ImageComponent.svelte';

export interface ImagePayload {
	altText: string;
	caption?: LexicalEditor;
	height?: number;
	key?: NodeKey;
	maxWidth?: number;
	showCaption?: boolean;
	src: string;
	width?: number;
	captionsEnabled?: boolean;
}
export type SerializedImageNode = Spread<
	{
		altText: string;
		caption: SerializedEditor;
		height?: number;
		maxWidth: number;
		showCaption: boolean;
		src: string;
		width?: number;
	},
	SerializedLexicalNode
>;
type DecoratorImageType = {
	componentClass: typeof SvelteComponent<any>;
	props: ComponentProps<ImageComponent>;
};

function isGoogleDocCheckboxImg(img: HTMLImageElement) {
	return (
		img.parentElement != null &&
		img.parentElement.tagName === 'LI' &&
		img.previousSibling === null &&
		img.getAttribute('aria-roledescription') === 'checkbox'
	);
}
function convertImageElement(domNode: HTMLImageElement) {
	const img = domNode;
	if (img.src.startsWith('file:///') || isGoogleDocCheckboxImg(img)) {
		return null;
	}
	const { alt: altText, src, width, height } = img;
	const node = $createImageNode({ altText, height, src, width });
	return { node };
}
export class ImageNode extends DecoratorNode<DecoratorImageType> {
	__src: string;
	__altText: string;
	__width: 'inherit' | number;
	__height: 'inherit' | number;
	__maxWidth: number;
	__showCaption: boolean;
	__caption: LexicalEditor;
	__captionsEnabled: boolean;
	static getType() {
		return 'image';
	}
	static clone(node: ImageNode) {
		return new ImageNode(
			node.__src,
			node.__altText,
			node.__maxWidth,
			node.__width,
			node.__height,
			node.__showCaption,
			node.__caption,
			node.__captionsEnabled,
			node.__key
		);
	}
	static importJSON(serializedNode: SerializedImageNode) {
		const { altText, height, width, maxWidth, caption, src, showCaption } = serializedNode;
		const node = $createImageNode({
			altText,
			height,
			maxWidth,
			showCaption,
			src,
			width
		});
		const nestedEditor = node.__caption;
		const editorState = nestedEditor.parseEditorState(caption.editorState);
		if (!editorState.isEmpty()) {
			nestedEditor.setEditorState(editorState);
		}
		return node;
	}
	exportDOM(): DOMExportOutput {
		const element = document.createElement('img');
		element.setAttribute('src', this.__src);
		element.setAttribute('alt', this.__altText);
		element.setAttribute('width', this.__width.toString());
		element.setAttribute('height', this.__height.toString());
		return { element };
	}
	static importDOM(): DOMConversionMap<HTMLImageElement> {
		return {
			img: () => ({
				conversion: convertImageElement,
				priority: 0 as 0 | 1 | 2 | 3 | 4 | undefined
			})
		};
	}
	constructor(
		src: string,
		altText: string,
		maxWidth: number,
		width?: number | 'inherit',
		height?: number | 'inherit',
		showCaption?: boolean,
		caption?: LexicalEditor,
		captionsEnabled?: boolean,
		key?: NodeKey
	) {
		super(key);
		this.__src = src;
		this.__altText = altText;
		this.__maxWidth = maxWidth;
		this.__width = width || 'inherit';
		this.__height = height || 'inherit';
		this.__showCaption = showCaption || false;
		this.__caption =
			caption ||
			createEditor({
				nodes: []
			});
		this.__captionsEnabled = captionsEnabled || captionsEnabled === undefined;
	}
	exportJSON() {
		return {
			altText: this.getAltText(),
			caption: this.__caption.toJSON(),
			height: this.__height === 'inherit' ? 0 : this.__height,
			maxWidth: this.__maxWidth,
			showCaption: this.__showCaption,
			src: this.getSrc(),
			type: 'image',
			version: 1,
			width: this.__width === 'inherit' ? 0 : this.__width
		};
	}
	setWidthAndHeight(width: 'inherit' | number, height: 'inherit' | number): void {
		const writable = this.getWritable();
		writable.__width = width;
		writable.__height = height;
	}
	setShowCaption(showCaption: boolean): void {
		const writable = this.getWritable();
		writable.__showCaption = showCaption;
	}
	// View
	createDOM(config: EditorConfig) {
		const span = document.createElement('span');
		const theme = config.theme;
		const className = theme.image;
		if (className !== undefined) {
			span.className = className;
		}
		return span;
	}
	updateDOM() {
		return false;
	}
	getSrc() {
		return this.__src;
	}
	getAltText() {
		return this.__altText;
	}
	// eslint-disable-next-line @typescript-eslint/no-unused-vars
	decorate(editor: LexicalEditor, config: EditorConfig): DecoratorImageType {
		return {
			componentClass: ImageComponent,
			props: {
				src: this.__src,
				altText: this.__altText,
				width: this.__width,
				height: this.__height,
				maxWidth: this.__maxWidth,
				nodeKey: this.__key,
				showCaption: this.__showCaption,
				caption: this.__caption,
				captionsEnabled: this.__captionsEnabled,
				resizable: true,
				editor: editor
			}
		};
	}
}
export function $createImageNode({
	altText,
	height,
	maxWidth = 500,
	captionsEnabled,
	src,
	width,
	showCaption,
	caption,
	key
}: ImagePayload): ImageNode {
	return $applyNodeReplacement(
		new ImageNode(src, altText, maxWidth, width, height, showCaption, caption, captionsEnabled, key)
	);
}
export function $isImageNode(node: LexicalNode | null | undefined): node is ImageNode {
	return node instanceof ImageNode;
}
