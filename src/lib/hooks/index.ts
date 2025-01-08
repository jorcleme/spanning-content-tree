import type { Editor } from '@tiptap/core';

export const useTextMenuCommands = (editor: Editor) => {
	const onBold = () => editor.chain().focus().toggleBold().run();
	const onItalic = () => editor.chain().focus().toggleItalic().run();
	const onStrike = () => editor.chain().focus().toggleStrike().run();
	const onUnderline = () => editor.chain().focus().toggleUnderline().run();
	const onCode = () => editor.chain().focus().toggleCode().run();
	const onCodeBlock = () => editor.chain().focus().toggleCodeBlock().run();

	const onSubscript = () => editor.chain().focus().toggleSubscript().run();
	const onSuperscript = () => editor.chain().focus().toggleSuperscript().run();
	const onAlignLeft = () => editor.chain().focus().setTextAlign('left').run();
	const onAlignCenter = () => editor.chain().focus().setTextAlign('center').run();
	const onAlignRight = () => editor.chain().focus().setTextAlign('right').run();
	const onAlignJustify = () => editor.chain().focus().setTextAlign('justify').run();

	const onChangeColor = (color: string) => editor.chain().setColor(color).run();
	const onClearColor = () => editor.chain().focus().unsetColor().run();

	const onChangeHighlight = (color: string) => editor.chain().setHighlight({ color }).run();
	const onClearHighlight = () => editor.chain().focus().unsetHighlight().run();

	return {
		onBold,
		onItalic,
		onStrike,
		onUnderline,
		onCode,
		onCodeBlock,
		onSubscript,
		onSuperscript,
		onAlignLeft,
		onAlignCenter,
		onAlignRight,
		onAlignJustify,
		onChangeColor,
		onClearColor,
		onChangeHighlight,
		onClearHighlight
	};
};
