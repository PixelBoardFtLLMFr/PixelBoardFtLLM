<template>
    <div class="debugContainer">
        <p v-for="i in maxLines" class="debugLine"> {{ debugLines[i-1] }}</p>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { debugLines } from '../logger'

const maxLines = ref(5);

</script>

<style scoped>
.debugContainer {
    position: absolute;
    bottom: 0px;
    left: 0px;
    display: flex;
    flex-direction: column-reverse;
}

.debugLine {
    color: red;
    margin: 0px;
    text-align: left;
}
</style>