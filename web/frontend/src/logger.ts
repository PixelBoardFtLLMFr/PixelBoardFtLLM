import { Ref, ref } from 'vue';

const debugLines = <Ref<string[]>> ref([]);
const messageTimeout = 5;

const log = (line : string) => {
    debugLines.value.unshift(line)
    setTimeout(() => {
        debugLines.value.pop()
    }, 1000 * messageTimeout);
}

export { debugLines, log}