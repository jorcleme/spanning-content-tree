import forms from '@tailwindcss/forms';
import typeography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
	darkMode: 'class',
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				white: '#FFFFFF',
				gray: {
					50: '#F7F7F7',
					100: '#F0F1F2',
					200: '#E1E4E8',
					300: '#D0D4D9',
					350: '#C1C6CC',
					400: '#A7ADB5',
					450: '#979FA8',
					500: '#889099',
					550: '#7E868F',
					600: '#6F7680',
					650: '#656C75',
					700: '#596069',
					750: '#464C54',
					800: 'var(--color-gray-800, #373C42)',
					850: 'var(--color-gray-850, #23282E)',
					900: 'var(--color-gray-900, #171717)',
					950: 'var(--color-gray-950, #0F1214)'
				},
				blue: {
					50: '#E3EEFF', // --hbr-color-blue-95 (lightest)
					100: '#CCE1FF', // --hbr-color-blue-90
					200: '#BAD6FF', // --hbr-color-blue-85
					300: '#A3C8FF', // --hbr-color-blue-80
					400: '#7CADF7', // --hbr-color-blue-70
					500: '#649EF5', // --hbr-color-blue-65
					600: '#5191F0', // --hbr-color-blue-60
					700: '#3E84E5', // --hbr-color-blue-55
					800: '#2774D9', // --hbr-color-blue-50
					850: '#1D69CC', // --hbr-color-blue-45 (extra slot)
					900: '#0D5CBD', // --hbr-color-blue-40
					950: '#0051AF' // --hbr-color-blue-35 (darkest)
				},
				red: {
					50: '#FFE8E9', // --hbr-color-red-95 (lightest)
					100: '#FFD4D5', // --hbr-color-red-90
					200: '#FFC7C9', // --hbr-color-red-85
					300: '#FFB2B5', // --hbr-color-red-80
					400: '#FF878B', // --hbr-color-red-70
					500: '#FF6E72', // --hbr-color-red-65
					600: '#FA5762', // --hbr-color-red-60
					700: '#EB4651', // --hbr-color-red-55
					800: '#D93843', // --hbr-color-red-50
					850: '#CC2D37', // --hbr-color-red-45 (extra slot)
					900: '#B2242D', // --hbr-color-red-40
					950: '#A01D26' // --hbr-color-red-35 (darkest)
				},
				orange: {
					50: '#FFEADB', // --hbr-color-orange-95 (lightest)
					100: '#FFD9BF', // --hbr-color-orange-90
					200: '#FCC9A7', // --hbr-color-orange-85
					300: '#FCB88D', // --hbr-color-orange-80
					400: '#FC8D4C', // --hbr-color-orange-70
					500: '#F7782F', // --hbr-color-orange-65
					600: '#F26722', // --hbr-color-orange-60
					700: '#D95A1A', // --hbr-color-orange-55
					800: '#C44F14', // --hbr-color-orange-50
					850: '#BA400B', // --hbr-color-orange-45 (extra slot)
					900: '#AD3907', // --hbr-color-orange-40
					950: '#942E03' // --hbr-color-orange-35 (darkest)
				},
				yellow: {
					50: '#FAEFB9', // --hbr-color-yellow-95 (lightest)
					100: '#F5E08E', // --hbr-color-yellow-90
					200: '#F2D268', // --hbr-color-yellow-85
					300: '#F2C13A', // --hbr-color-yellow-80
					400: '#E0A419', // --hbr-color-yellow-70
					500: '#D6900D', // --hbr-color-yellow-65
					600: '#CC8604', // --hbr-color-yellow-60
					700: '#BD7202', // --hbr-color-yellow-55
					800: '#B05F04', // --hbr-color-yellow-50
					850: '#A65503', // --hbr-color-yellow-45 (extra slot)
					900: '#944B03', // --hbr-color-yellow-40
					950: '#804103' // --hbr-color-yellow-35 (darkest)
				},
				lime: {
					50: '#EAF2D3', // --hbr-color-lime-95 (lightest)
					100: '#D7E8A9', // --hbr-color-lime-90
					200: '#C7DE8A', // --hbr-color-lime-85
					300: '#B5D166', // --hbr-color-lime-80
					400: '#B5D166', // --hbr-color-lime-70
					500: '#89AB2C', // --hbr-color-lime-65
					600: '#7DA11B', // --hbr-color-lime-60
					700: '#6C8C14', // --hbr-color-lime-55
					800: '#61800E', // --hbr-color-lime-50
					850: '#577309', // --hbr-color-lime-45 (extra slot)
					900: '#4C6605', // --hbr-color-lime-40
					950: '#425902' // --hbr-color-lime-35 (darkest)
				},
				green: {
					50: '#E0F5D5', // --hbr-color-green-95 (lightest)
					100: '#C5EBB2', // --hbr-color-green-90
					200: '#B0E396', // --hbr-color-green-85
					300: '#98D977', // --hbr-color-green-80
					400: '#6BBF41', // --hbr-color-green-70
					500: '#5EB035', // --hbr-color-green-65
					600: '#52A62B', // --hbr-color-green-60
					700: '#45991F', // --hbr-color-green-55
					800: '#398519', // --hbr-color-green-50
					850: '#2B7A0C', // --hbr-color-green-45 (extra slot)
					900: '#266B0B', // --hbr-color-green-40
					950: '#1F5E06' // --hbr-color-green-35 (darkest)
				},
				emerald: {
					50: '#D4F5E1', // --hbr-color-emerald-95 (lightest)
					100: '#B6EDCC', // --hbr-color-emerald-90
					200: '#97E5B8', // --hbr-color-emerald-85
					300: '#75D9A0', // --hbr-color-emerald-80
					400: '#4CBF7F', // --hbr-color-emerald-70
					500: '#36B26E', // --hbr-color-emerald-65
					600: '#21A65F', // --hbr-color-emerald-60
					700: '#169855', // --hbr-color-emerald-55
					800: '#0F874C', // --hbr-color-emerald-50
					850: '#0B7B46', // --hbr-color-emerald-45 (extra slot)
					900: '#087041', // --hbr-color-emerald-40
					950: '#075E39' // --hbr-color-emerald-35 (darkest)
				},
				teal: {
					50: '#D5F5F5', // --hbr-color-teal-95 (lightest)
					100: '#A9EBEB', // --hbr-color-teal-90
					200: '#84E3E3', // --hbr-color-teal-85
					300: '#4AD9D9', // --hbr-color-teal-80
					400: '#17C2C2', // --hbr-color-teal-70
					500: '#0BB2B8', // --hbr-color-teal-65
					600: '#04A4B0', // --hbr-color-teal-60
					700: '#028E99', // --hbr-color-teal-55
					800: '#01818C', // --hbr-color-teal-50
					850: '#017580', // --hbr-color-teal-45 (extra slot)
					900: '#006773', // --hbr-color-teal-40
					950: '#005C66' // --hbr-color-teal-35 (darkest)
				},
				sky: {
					50: '#D9F4FF', // --hbr-color-lightblue-95 (lightest)
					100: '#B5E9FF', // --hbr-color-lightblue-90
					200: '#9ADFFC', // --hbr-color-lightblue-85
					300: '#6FD2FC', // --hbr-color-lightblue-80
					400: '#33BBF5', // --hbr-color-lightblue-70
					500: '#23A8EB', // --hbr-color-lightblue-65
					600: '#139BEB', // --hbr-color-lightblue-60
					700: '#0D8BD4', // --hbr-color-lightblue-55
					800: '#087ABD', // --hbr-color-lightblue-50
					850: '#0570AD', // --hbr-color-lightblue-45 (extra slot)
					900: '#03639C', // --hbr-color-lightblue-40
					950: '#015788' // --hbr-color-lightblue-35 (darkest)
				},
				lavender: {
					50: '#EBEDFF', // --hbr-color-lavender-95 (lightest)
					100: '#D9DDFF', // --hbr-color-lavender-90
					200: '#CCD1FF', // --hbr-color-lavender-85
					300: '#BAC1FF', // --hbr-color-lavender-80
					400: '#9CA6FF', // --hbr-color-lavender-70
					500: '#8A95FF', // --hbr-color-lavender-65
					600: '#7D8AFF', // --hbr-color-lavender-60
					700: '#6977F0', // --hbr-color-lavender-55
					800: '#5A68E5', // --hbr-color-lavender-50
					850: '#505ED9', // --hbr-color-lavender-45 (extra slot)
					900: '#4653C7', // --hbr-color-lavender-40
					950: '#3B47B2' // --hbr-color-lavender-35 (darkest)
				},
				slate: {
					50: '#EBEDFF', // --hbr-color-slate-95 (lightest)
					100: '#D9DEFA', // --hbr-color-slate-90
					200: '#CED3F2', // --hbr-color-slate-85
					300: '#C1C6E8', // --hbr-color-slate-80
					400: '#A3AAD6', // --hbr-color-slate-70
					500: '#959CCC', // --hbr-color-slate-65
					600: '#868EC2', // --hbr-color-slate-60
					700: '#767EB2', // --hbr-color-slate-55
					800: '#6871A3', // --hbr-color-slate-50
					850: '#5D6596', // --hbr-color-slate-45 (extra slot)
					900: '#545C8A', // --hbr-color-slate-40
					950: '#484F7A' // --hbr-color-slate-35 (darkest)
				},
				purple: {
					50: '#F3EBFF', // --hbr-color-purple-95 (lightest)
					100: '#E8D9FF', // --hbr-color-purple-90
					200: '#E0CCFF', // --hbr-color-purple-85
					300: '#D6BAFF', // --hbr-color-purple-80
					400: '#C299FF', // --hbr-color-purple-70
					500: '#B587FA', // --hbr-color-purple-65
					600: '#A974F7', // --hbr-color-purple-60
					700: '#9B5FF5', // --hbr-color-purple-55
					800: '#8D4EED', // --hbr-color-purple-50
					850: '#864AE0', // --hbr-color-purple-45 (extra slot)
					900: '#753BCC', // --hbr-color-purple-40
					950: '#6732B8' // --hbr-color-purple-35 (darkest)
				},
				magenta: {
					50: '#FFE8F9', // --hbr-color-magenta-95 (lightest)
					100: '#FFD1F3', // --hbr-color-magenta-90
					200: '#FAC5ED', // --hbr-color-magenta-85
					300: '#F7B0E5', // --hbr-color-magenta-80
					400: '#F582D8', // --hbr-color-magenta-70
					500: '#F26DD1', // --hbr-color-magenta-65
					600: '#E85FC6', // --hbr-color-magenta-60
					700: '#D64BB3', // --hbr-color-magenta-55
					800: '#C23EA1', // --hbr-color-magenta-50
					850: '#B53394', // --hbr-color-magenta-45 (extra slot)
					900: '#A62686', // --hbr-color-magenta-40
					950: '#941B76' // --hbr-color-magenta-35 (darkest)
				},
				pink: {
					50: '#FFE8EF', // --hbr-color-pink-95 (lightest)
					100: '#FFD4E0', // --hbr-color-pink-90
					200: '#FFC4D5', // --hbr-color-pink-85
					300: '#FCB3C8', // --hbr-color-pink-80
					400: '#FF87A9', // --hbr-color-pink-70
					500: '#F57398', // --hbr-color-pink-65
					600: '#F2638C', // --hbr-color-pink-60
					700: '#E3447C', // --hbr-color-pink-55
					800: '#CF3A7A', // --hbr-color-pink-50
					850: '#C2306F', // --hbr-color-pink-45 (extra slot)
					900: '#B02863', // --hbr-color-pink-40
					950: '#991D53' // --hbr-color-pink-35 (darkest)
				}
			},
			fontFamily: {
				inter: ['Inter', 'sans-serif'],
				archivo: ['Archivo', 'sans-serif'],
				'mona-sans': ['Mona Sans', 'sans-serif'],
				CiscoSans: ['CiscoSans', 'sans-serif'],
				CiscoSansLight: ['CiscoSansLight', 'sans-serif']
			},
			typography: {
				DEFAULT: {
					css: {
						pre: false,
						code: false,
						'pre code': false,
						'code::before': false,
						'code::after': false
					}
				}
			}
		}
	},
	plugins: [typeography, forms]
};
