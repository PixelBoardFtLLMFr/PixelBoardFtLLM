<template>
    <img src="../assets/settingIcon.svg" class="settingIcon" @click="switchShowSettings" v-if="!showSettings">
    <div class="settingContainer" v-if="showSettings">
        <img src="../assets/cancelIcon.svg" class="settingIcon" @click="switchShowSettings">
        <div class="inputField">
            <input type="range" min="1" max="10" id="framerateInput" v-model="framerate">
            <label for="framerateInput"> Framerate : {{ framerate }} </label>
        </div>
        <div class="inputField">
            <input type="text" id="keyInput" v-model="apiKey">
            <label for="keyInput"> API Key </label>
        </div>
        <div class="inputField">
            <select id="languageInput" v-model="recognitionLanguage" @change="$emit('changeLanguage')">
                <option v-for="language in languages" :value="language[1]"> {{ language[0] }}</option>
            </select>
            <label for="languageInput"> Recognized language </label>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { framerate } from '../penguin'
import { apiKey, recognitionLanguage } from '../api'

const showSettings = ref(false)

const emit = defineEmits(['changeLanguage'])

const switchShowSettings = () => {
    showSettings.value = !showSettings.value
}

const languages = ref([
    ["Chinese", "zh-CN"],
    ["English", "en-US"],
    ["French", "fr-FR"],
    ["German", "de-DE"],
    ["Indonesian", "id-ID"],
    ["Japanese", "ja-JP"],
    ["Spanish", "es-ES"],
    ["Thai", "th-TH"],
    ["Vietnamese", "vi-VN"]
]);

</script>

<style scoped>
.settingIcon {
    position: absolute;
    top: 0px;
    right: 0px;
    width: 50px;
    margin: 1rem;
    z-index: 10;
}

.settingIcon {
    cursor: pointer;
}

.settingContainer {
    position: absolute;
    padding-top: 8vh;
    top: 0px;
    right: 0px;
    height: 100vh;
    width: 20vw;
    display: flex;
    flex-direction: column;
    background-color: rgba(100,100,100, 0.5);
}

.inputField {
    font-size: 1.5em;
    color: white;
    width: 100%;
    display: flex;
    flex-direction: row;
    align-items: center;
    margin: 20px;
    gap: 20px;
}

.inputField > * {
    font-size: medium;
}
</style>