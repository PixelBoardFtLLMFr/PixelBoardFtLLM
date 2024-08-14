<script setup lang="ts">
import IKCanvas from './components/IKCanvas.vue'
import SettingTab from './components/SettingTab.vue'
import InputTab from "./components/InputTab.vue"
import DebugTab from "./components/DebugTab.vue"
import {ref} from 'vue'

const canvas : null | any = ref(null)
const inputTab : null | any = ref(null)

const showPrompt = (prompt : string) => {
  if (canvas.value)
    canvas.value.animateFromPrompt(prompt)
}

const updateLanguage = () => {
  if (inputTab.value)
    inputTab.value.updateLanguage()
}

</script>

<template>
  <InputTab @submit-prompt="showPrompt" ref="inputTab" />
  <IKCanvas id="mainCanvas" ref="canvas"/>
  <SettingTab @change-language="updateLanguage"/>
  <DebugTab/>
</template>

<style>
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

#mainCanvas {
  width: 100vh;  /* Assure que le canvas est carré en prenant la hauteur de la fenêtre */
  height: 100vh; /* Hauteur de la fenêtre */
  background-color: #000000;
  display: inline-block;
}

.mainContainer {
  display: flex;
  justify-content: center;
  width: 100vw;
}

</style>