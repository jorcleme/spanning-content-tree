/* eslint-disable @typescript-eslint/ban-types */
import { Mark, mergeAttributes } from '@tiptap/core';

export interface UnderlineOptions {
	/**
	 * HTML attributes to add to the underline element.
	 * @default {}
	 * @example { class: 'foo' }
	 */
	HTMLAttributes: Record<string, any>;
}

declare module '@tiptap/core' {
	interface Commands<ReturnType> {
		underline: {
			/**
			 * Set an underline mark
			 * @example editor.commands.setUnderline()
			 */
			setUnderline: () => ReturnType;
			/**
			 * Toggle an underline mark
			 * @example editor.commands.toggleUnderline()
			 */
			toggleUnderline: () => ReturnType;
			/**
			 * Unset an underline mark
			 * @example editor.commands.unsetUnderline()
			 */
			unsetUnderline: () => ReturnType;
		};
	}
}

/**
 * This extension allows you to create underline text.
 * @see https://www.tiptap.dev/api/marks/underline
 */
export const Underline = Mark.create<UnderlineOptions>({
	name: 'underline',

	addOptions() {
		return {
			HTMLAttributes: {}
		};
	},

	parseHTML() {
		return [
			{
				tag: 'u'
			},
			{
				style: 'text-decoration',
				consuming: false,
				getAttrs: (style) => ((style as string).includes('underline') ? {} : false)
			}
		];
	},

	renderHTML({ HTMLAttributes }) {
		return ['u', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0];
	},

	addCommands() {
		return {
			setUnderline:
				() =>
				({ commands }) => {
					return commands.setMark(this.name);
				},
			toggleUnderline:
				() =>
				({ commands }) => {
					return commands.toggleMark(this.name);
				},
			unsetUnderline:
				() =>
				({ commands }) => {
					return commands.unsetMark(this.name);
				}
		};
	},

	addKeyboardShortcuts() {
		return {
			'Mod-u': () => this.editor.commands.toggleUnderline(),
			'Mod-U': () => this.editor.commands.toggleUnderline()
		};
	}
});


import { Mark, mergeAttributes } from '@tiptap/core'
import type { StyleParseRule } from '@tiptap/pm/model'

export interface SubscriptExtensionOptions {
  /**
   * HTML attributes to add to the subscript element.
   * @default {}
   * @example { class: 'foo' }
   */
  // eslint-disable-next-line @typescript-eslint/ban-types
  HTMLAttributes: Object,
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    subscript: {
      /**
       * Set a subscript mark
       * @example editor.commands.setSubscript()
       */
      setSubscript: () => ReturnType,
      /**
       * Toggle a subscript mark
       * @example editor.commands.toggleSubscript()
       */
      toggleSubscript: () => ReturnType,
      /**
       * Unset a subscript mark
       * @example editor.commands.unsetSubscript()
       */
      unsetSubscript: () => ReturnType,
    }
  }
}

/**
 * This extension allows you to create subscript text.
 * @see https://www.tiptap.dev/api/marks/subscript
 */
export const Subscript = Mark.create<SubscriptExtensionOptions>({
  name: 'subscript',

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  parseHTML() {
    return [
      {
        tag: 'sub',
      },
      {
        style: 'vertical-align',
        getAttrs(value) {
          // Don’t match this rule if the vertical align isn’t sub.
          if (value !== 'sub') {
            return false
          }

          // If it falls through we’ll match, and this mark will be applied.
          return null
        },
      } as StyleParseRule,
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['sub', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0]
  },

  addCommands() {
    return {
      setSubscript: () => ({ commands }) => {
        return commands.setMark(this.name)
      },
      toggleSubscript: () => ({ commands }) => {
        return commands.toggleMark(this.name)
      },
      unsetSubscript: () => ({ commands }) => {
        return commands.unsetMark(this.name)
      },
    }
  },

  addKeyboardShortcuts() {
    return {
      'Mod-,': () => this.editor.commands.toggleSubscript(),
    }
  },
})

import { Mark, mergeAttributes } from '@tiptap/core'
import type { StyleParseRule } from '@tiptap/pm/model'

export interface SuperscriptExtensionOptions {
  /**
   * HTML attributes to add to the superscript element.
   * @default {}
   * @example { class: 'foo' }
   */
  HTMLAttributes: Object,
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    superscript: {
      /**
       * Set a superscript mark
       * @example editor.commands.setSuperscript()
       */
      setSuperscript: () => ReturnType,
      /**
       * Toggle a superscript mark
       * @example editor.commands.toggleSuperscript()
       */
      toggleSuperscript: () => ReturnType,
      /**
       * Unset a superscript mark
       *  @example editor.commands.unsetSuperscript()
       */
      unsetSuperscript: () => ReturnType,
    }
  }
}

/**
 * This extension allows you to create superscript text.
 * @see https://www.tiptap.dev/api/marks/superscript
 */
export const Superscript = Mark.create<SuperscriptExtensionOptions>({
  name: 'superscript',

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  parseHTML() {
    return [
      {
        tag: 'sup',
      },
      {
        style: 'vertical-align',
        getAttrs(value) {
          // Don’t match this rule if the vertical align isn’t super.
          if (value !== 'super') {
            return false
          }

          // If it falls through we’ll match, and this mark will be applied.
          return null
        },
      } as StyleParseRule,
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return ['sup', mergeAttributes(this.options.HTMLAttributes, HTMLAttributes), 0]
  },

  addCommands() {
    return {
      setSuperscript: () => ({ commands }) => {
        return commands.setMark(this.name)
      },
      toggleSuperscript: () => ({ commands }) => {
        return commands.toggleMark(this.name)
      },
      unsetSuperscript: () => ({ commands }) => {
        return commands.unsetMark(this.name)
      },
    }
  },

  addKeyboardShortcuts() {
    return {
      'Mod-.': () => this.editor.commands.toggleSuperscript(),
    }
  },
})


declare module '@tiptap/core' {
    interface Commands<ReturnType> {
      textAlign: {
        /**
         * Set the text align attribute
         * @param alignment The alignment
         * @example editor.commands.setTextAlign('left')
         */
        setTextAlign: (alignment: string) => ReturnType,
        /**
         * Unset the text align attribute
         * @example editor.commands.unsetTextAlign()
         */
        unsetTextAlign: () => ReturnType,
      }
    }

    interface Commands<ReturnType> {
        highlight: {
          /**
           * Set a highlight mark
           * @param attributes The highlight attributes
           * @example editor.commands.setHighlight({ color: 'red' })
           */
          setHighlight: (attributes?: { color: string }) => ReturnType,
          /**
           * Toggle a highlight mark
           * @param attributes The highlight attributes
           * @example editor.commands.toggleHighlight({ color: 'red' })
           */
          toggleHighlight: (attributes?: { color: string }) => ReturnType,
          /**
           * Unset a highlight mark
           * @example editor.commands.unsetHighlight()
           */
          unsetHighlight: () => ReturnType,
        }
      }

      interface Commands<ReturnType> {
        fontFamily: {
          /**
           * Set the font family
           * @param fontFamily The font family
           * @example editor.commands.setFontFamily('Arial')
           */
          setFontFamily: (fontFamily: string) => ReturnType,
          /**
           * Unset the font family
           * @example editor.commands.unsetFontFamily()
           */
          unsetFontFamily: () => ReturnType,
        }
      }
  }
