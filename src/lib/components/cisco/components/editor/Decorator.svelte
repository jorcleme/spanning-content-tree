<script lang="ts">
	import { SvelteComponent, getAllContexts, onMount } from 'svelte';
	import { getEditor } from '$lib/utils/editor';
	import { mergeRegister } from '@lexical/utils';
	import { DecoratorNode } from 'lexical';

	type RegisteredComponents = Record<string, SvelteComponent>;

	const contexts = getAllContexts();
	const editor = getEditor();
	const components: RegisteredComponents = {};
	const dirtyComponents: string[] = [];
	onMount(() => {
		const unregisterCallBacks: Array<(...args: any[]) => void> = [];
		editor._nodes.forEach((n) => {
			if (n.klass.prototype instanceof DecoratorNode) {
				let unreg = editor.registerMutationListener(n.klass, (nodes, payload) => {
					for (let [key, val] of nodes) {
						if (val === 'destroyed') {
							delete components[key];
						} else {
							dirtyComponents.push(key);
						}
					}
				});
				unregisterCallBacks.push(unreg);
			}
		});
		return mergeRegister(
			...unregisterCallBacks,
			// register Decorator listener to render nodes
			// use dirty nodes identified by the mutation listener
			// 1- set `props` on existing svelte components
			// 2- create new components and put them in cache
			editor.registerDecoratorListener((decorators: Record<string, SvelteComponent>) => {
				dirtyComponents.forEach((nodeKey) => {
					const decorator = decorators[nodeKey];
					const com = components[nodeKey];
					const element = editor.getElementByKey(nodeKey);
					if (element?.innerHTML && com) {
						com.$set(decorator.props);
					} else if (element) {
						components[nodeKey] = new decorator.componentClass({
							target: element,
							props: decorator.props,
							context: contexts
						});
					}
				});
				dirtyComponents.length = 0;
			})
		);
	});
</script>
