import axios from "axios";
import { Color, newColor, white } from "./color";
import { ref } from "vue";
import { log } from "./logger";

const backIP = "127.0.0.1"
const backPort = 4444

const apiKey = ref("");
const recognitionLanguage = ref("en-US")

type LLMData = {
    ARM: {
        left: number[];
        right: number[];
    };
    EYE: null | Color[][];
    FACE: string;
    HEAD: number[][];
    LEG: {
        left: number[];
        right: number[];
    }
    PARTICLE: string;
}

type AngleData = {
    ARM: {
        left: number;
        right: number;
    };
    LEG: {
        left: number;
        right: number;
    }
    HEAD: number;
}

const sendPrompt = (prompt : string, callback : (response : any) => void) => {
    axios.post(`https://${backIP}:${backPort}/`, {
        key: apiKey.value,
        input: prompt
    }).then(callback).catch((e) => {
        log("Error while communicating with the server. Be sure the server is running and the OpenAPI key is valid.")
    })
}

const toLLMData = (response : any) => {
    let eye : Color[][] | null = null;
    if (response.EYE !== null) {
        
        eye = [
            [white, white, white],
            [white, white, white],
            [white, white, white],
        ]
        for (let y = 0 ; y < 3 ; y++) {
            for (let x = 0 ; x < 3 ; x++) {
                eye[y][x] = newColor(response.EYE[y][x][0], response.EYE[y][x][1], response.EYE[y][x][2])
            }
        }
    }
    return <LLMData> {
        ARM: {
            left: response.ARM.left,
            right: response.ARM.right,
        },
        EYE: eye,
        FACE: response.FACE,
        HEAD: response.HEAD,
        LEG: {
            left: response.LEG.left,
            right: response.LEG.right,
        },
        PARTICLE: response.PARTICLE,
    }
}

const extractAngle = (data : LLMData, frame : number) : AngleData => {
    return <AngleData> {
        ARM: {
            left: data.ARM.left[frame],
            right: data.ARM.right[frame]
        },
        LEG: {
            left: data.LEG.left[frame],
            right: data.LEG.right[frame]
        },
        HEAD: data.HEAD[frame][0]
    }
}  

export type { LLMData, AngleData }
export { sendPrompt, extractAngle, toLLMData, apiKey, recognitionLanguage }