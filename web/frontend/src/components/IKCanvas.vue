<template>
    <div class="canvasContainer">
        <canvas id="simulationCanvas" :width="canvasWidth" :height="canvasHeight">
        </canvas>
    </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { Image, newImage } from '../image'
import { drawPenguin, drawDefaultPenguin, framerate } from '../penguin'
import { LLMData, sendPrompt, toLLMData } from '../api';
import { addSpecialEffect, loadParticles } from '../specialEffects'

const canvasWidth = ref(1000);
const canvasHeight = ref(1000);

let canvas : HTMLCanvasElement | null = null;
let ctx : CanvasRenderingContext2D | null = null;

const animateFromPrompt = (prompt : string) => {
    const animate = (response : any) => {
        const data : LLMData = toLLMData(response.data)
        console.log(data)
        nextFrame(data, 0)
    }
    sendPrompt(prompt, animate)
}

const displayPixels = (image : Image) => {
    if (!canvas || !ctx)
        return;
    const pixels = image.pixels
    const pixelHeight = Math.floor(canvasHeight.value / image.height)
    const pixelWidth = Math.floor(canvasWidth.value / image.width)
    for (let y = 0; y < pixels.length; y++) {
        for (let x = 0; x < pixels[y].length; x++) {
            ctx.fillStyle = `rgb(${pixels[y][x].r}, ${pixels[y][x].g}, ${pixels[y][x].b})`
            ctx.fillRect(x * pixelWidth, y * pixelHeight, pixelWidth, pixelHeight);
        }
    }
}

const initCanvas = () => {
    canvas = <HTMLCanvasElement> document.getElementById("simulationCanvas");
    ctx = canvas.getContext("2d");
}

const nextFrame = async (data : LLMData, frameIndex : number) => {
    if (frameIndex >= data.ARM.left.length) {
        return;
    }
    const image = newImage(25, 25)
    drawPenguin(image, data, frameIndex);
    await addSpecialEffect(image, data.PARTICLE);
    displayPixels(image);
    setTimeout(() => {
        nextFrame(data, frameIndex + 1)
    }, Math.floor(1000 / framerate.value))
}

onMounted(async () => {
    initCanvas();
    loadParticles();
    const image = newImage(25, 25);
    drawDefaultPenguin(image);
    displayPixels(image);    
})

defineExpose({
    animateFromPrompt
});

</script>

<style scoped>
.canvasContainer {
    margin: 0;
    padding: 0;
}

#simulationCanvas {
    display: block;
    height : 100vh;
    margin: 0;
    padding: 0;
}
</style>