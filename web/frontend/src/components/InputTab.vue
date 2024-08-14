<template>
    <div class="iconContainer">
        <div class="microphoneContainer" @click="switchMicrophone">
            <img src="../assets/cancelIconRed.svg" id="cancelMicrophone" v-if="!microphoneOn">
            <img src="../assets/microphone.svg" id="microphoneIcon">
        </div>
        <img src="../assets/pencil.svg" id="pencilIcon" @click="switchModal">
    </div>
    <div class="modalContainer" v-if="modalInputOn" @click="switchModal">
        <div class="inputContainer" @click.stop="">
            <label for="promptInput"> Enter prompt</label>
            <textarea type="text" id="promptInput" v-model="inputPrompt"></textarea>
            <button id="submitPromptButton" @click="submitPrompt"> Submit </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { log } from '../logger'
import { recognitionLanguage } from '../api'

const modalInputOn = ref(false)
const inputPrompt = ref("")
const microphoneOn = ref(false)

let recognition : any | null = null;

const emit = defineEmits(['submitPrompt'])

const switchModal = () => {
    modalInputOn.value = !modalInputOn.value
}

const submitPrompt = () => {
    emit('submitPrompt', inputPrompt.value)
    inputPrompt.value = "";
    switchModal();
}

//@ts-ignore
const SpeechRecognition = (window.SpeechRecognition || window.webkitSpeechRecognition || window.mozSpeechRecognition || window.msSpeechRecognition) as typeof window.SpeechRecognition;

if (!SpeechRecognition) {
    log("Speech Recognition is not available on this browser. Try using another one (Chrome, Edge, Opera, etc...)")
}

const switchMicrophone = () => {
    if (!recognition) {
        microphoneOn.value = false;
        log("Speech Recognition is not available on this browser. Try using another one (Chrome, Edge, Opera, etc...)")
    } else {
        microphoneOn.value = !microphoneOn.value;
        switchRecognition(microphoneOn.value);
    }
}

const updateLanguage = () => {
    if (recognition) {
        recognition.lang = recognitionLanguage.value;
        recognition.stop();
    }
}

const switchRecognition = (activate : boolean) => {
    if (activate)
        startRecognition();
    else
        stopRecognition();
}

const startRecognition = () => {
    if (recognition) {
        recognition.onend = () => {
            recognition.start();
        }
        recognition.start();
    }
};

const stopRecognition = () => {
    if (recognition) {
        recognition.onend = () => { }
        recognition.stop()
    }
}

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = recognitionLanguage.value;
    
    recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        log(transcript);
        emit('submitPrompt', inputPrompt.value)
    };
    
}

defineExpose({
    updateLanguage
});

</script>

<style scoped>

.iconContainer {
    position: absolute;
    top: 0px;
    left: 0px;
    cursor: pointer;
    display: flex;
}

.microphoneContainer {
    position: relative;
    width: 50px;
    margin: 0.5rem;
}

.microphoneContainer > img {
    position: absolute;
    top: 0px;
    left: 0px;
}

.microphoneContainer:hover {
    animation: shake linear 0.3s;
}

.modalContainer {
    position: absolute;
    top: 0px;
    left: 0px;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 100;
    display: flex;
    justify-content: center;
}

.inputContainer {
    background-color: black;
    color: white;
    margin: auto;
    border-radius: 10px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    animation: fadeIn ease 0.2s;
}

@keyframes shake {
    25% {
        transform: rotate(-5deg)
    }
    75% {
        transform: rotate(5deg)
    }
    100% {
        transform: rotate(0deg);
    }
    
}

@keyframes fadeIn {
    0% {
        opacity: 0;
    }
    100% {
        opacity: 100;
    }
    
}

#promptInput {
    margin-top: 5px;
    height: 5rem;
    text-wrap: wrap;
    resize: none;
    background-color: whitesmoke;
}

#submitPromptButton {
    margin-top: 5px;
}

img {
    width: 50px;
    margin: 0.5rem;
}

#pencilIcon {
    width: 70px;
}

#pencilIcon:hover {
    animation: shake ease-in-out 0.3s;
}

#cancelMicrophone {
    left: 0px;
    top: -7px;
    z-index: 10;
}

</style>