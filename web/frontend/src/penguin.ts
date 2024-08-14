import { Image, drawRotatedEllipse, drawRotatedPolygon, drawRotatedRectangle } from "./image";
import { yellow, blue, white, orange, Color, bright, red } from "./color";
import { AngleData, LLMData, extractAngle } from "./api";
import { ref } from "vue";

const framerate = ref(5);

const size = 25
const height = 0

const body_width   = Math.floor(size * 0.4)
const body_height  = Math.floor(size * 0.4)
const head_size    = Math.floor(size * 0.5)
const eye_size     = Math.floor(size * 0.1)
const eye_x_offset = Math.floor(head_size * 0.3)
const eye_y_offset = Math.floor(head_size * 0.7)
const beak_size    = Math.floor(size * 0.2)
const foot_width   = Math.floor(size * 0.15)
const foot_height  = Math.floor(size * 0.1)
const arm_width    = Math.floor(size * 0.1)
const arm_height   = Math.floor(size * 0.4)

const body_x = Math.floor((size - body_width)  / 2)
const body_y = Math.floor(size / 2) - height
const head_x = body_x + Math.floor((body_width - head_size) / 2)
const head_y = body_y - head_size
const foot_y = body_y + body_height
const arm_y  = body_y

const head_cx = head_x + Math.floor(head_size / 2)
const head_cy = head_y + head_size

const eye_left_x1 = head_cx - eye_x_offset - Math.floor(eye_size / 2)
const eye_left_x2 = eye_left_x1 + Math.floor(eye_size / 2)
const eye_y1 = head_cy - eye_y_offset
const eye_y2 = head_cy - eye_y_offset + eye_size
const eye_right_x1 = head_cx + eye_x_offset - 2
const eye_right_x2 = eye_right_x1 + Math.floor(eye_size / 2)
const eye_points = [[[eye_left_x1, eye_y1], [eye_left_x2, eye_y2]],
                    [[eye_right_x1, eye_y1], [eye_right_x2, eye_y2]]]

const beak_x1 = head_cx - Math.floor(beak_size / 2)
const beak_x2 = head_cx + Math.floor(beak_size / 2)
const beak_x3 = head_cx
const beak_x4 = beak_x3
const beak_y1 = head_cy - beak_size + 1
const beak_y2 = beak_y1
const beak_y3 = beak_y1 + Math.floor(3 * beak_size / 4)
const beak_y4 = beak_y1 - Math.floor(beak_size / 4) + 1

const dx = Math.min(1, body_width * 0.1)
const dy = Math.min(1, body_width * 0.1)

const penguinMeasures = {
    size: size,
    height: height,
    body_width: body_width,
    body_height: body_height,
    head_size: head_size,
    eye_size: eye_size,
    eye_x_offset: eye_x_offset,
    eye_y_offset: eye_y_offset,
    beak_size: beak_size,
    foot_width: foot_width,
    foot_height: foot_height,
    arm_width: arm_width,
    arm_height: arm_height,
    body_x: body_x,
    body_y: body_y,
    head_x: head_x,
    head_y: head_y,
    foot_y: foot_y,
    arm_y: arm_y,
    head_cx: head_cx,
    head_cy: head_cy,
    eye_left_x1: eye_left_x1,
    eye_left_x2: eye_left_x2,
    eye_y1: eye_y1,
    eye_y2: eye_y2,
    eye_right_x1: eye_right_x1,
    eye_right_x2: eye_right_x2,
    eye_points: eye_points,
    beak_x1: beak_x1,
    beak_x2: beak_x2,
    beak_x3: beak_x3,
    beak_x4: beak_x4,
    beak_y1: beak_y1,
    beak_y2: beak_y2,
    beak_y3: beak_y3,
    beak_y4: beak_y4,
    dx: dx,
    dy: dy
}

const drawBody = (image : Image) => {
    drawRotatedEllipse(image,
        body_x,
        body_y - 2,
        body_x + body_width,
        body_y + body_height,
        0, 0, 0, blue)

    drawRotatedEllipse(image, 
        body_x + dx,
        body_y + dy - 2,
        body_x + body_width  - dx,
        body_y + body_height - dy,
        0, 0, 0, white)
}

const drawEyesFromMatrix = (image : Image, angle : number, eyes: Color[][]) => {
    for (let y = 0 ; y < 3 ; y++) {
        for (let x = 0 ; x < 3 ; x++) {
            drawRotatedRectangle(image, eye_left_x1 + x, eye_y1 + y, eye_left_x1 + x + 1, eye_y1 + y + 1, head_cx, head_cy, angle, eyes[y][x])
            drawRotatedRectangle(image, eye_right_x1 + x, eye_y1 + y, eye_right_x1 + x + 1, eye_y1 + y + 1, head_cx, head_cy, angle, eyes[y][x])
        }
    }
}

const defaultEyes : Record<string, Color[][]> = {
    "neutral": [
        [yellow, yellow, white],
        [yellow, yellow, white],
        [yellow, yellow, white]
    ],
    "sad": [
        [yellow, yellow, yellow],
        [white, blue, blue],
        [blue, white, white]
    ],
    "happy": [
        [white, yellow, white],
        [yellow, white, yellow],
        [white, white, white]
    ],
    "angry": [
        [bright, white, white],
        [red, bright, white],
        [red, bright, white]
    ],
    "surprised": [
        [white, yellow, white],
        [yellow, yellow, yellow],
        [white, yellow, white]
    ]
}

const drawEyesFromExpression = (image: Image, angle: number, expression: string) => {
    const matrix = defaultEyes[expression];
    if (matrix)
        drawEyesFromMatrix(image, angle, matrix)
}

const drawBeak = (image : Image, angle : number) => {
    drawRotatedPolygon(image,
        [[beak_x1, beak_y1], [beak_x3, beak_y3], [beak_x2, beak_y2], [beak_x4, beak_y4]],
        head_cx, head_cy, angle, orange
        )
}

const drawHead = (image : Image, angle : number, eyes : Color[][] | null, expression : string) => {
    drawRotatedEllipse(image,
                         head_x, head_y,
                         head_size + head_x, head_size + head_y,
                         head_cx, head_cy,
                         angle,
                         blue)

    drawRotatedEllipse(image,
                         head_x + 1, head_y + 1,
                         head_size + head_x - 1, head_size + head_y - 1,
                         head_cx, head_cy,
                         angle,
                         white)

    drawRotatedRectangle(image, body_x + 2*dx + 1,
                         body_y - dy,
                         body_x + body_width - 2*dx - 1,
                         body_y, 0, 0, 0,
                         white)
    
    drawBeak(image, angle)
    if (eyes === null)
        drawEyesFromExpression(image, angle, expression);
    else
        drawEyesFromMatrix(image, angle, eyes)
}

const drawFeet = (image : Image, angle_left : number, angle_right : number) => {
    const foot_left_x1 = body_x
    const foot_left_y1 = foot_y
    const foot_left_x2 = foot_left_x1 + foot_width
    const foot_left_y2 = foot_left_y1 + foot_height

    drawRotatedRectangle(image,
                            foot_left_x1, foot_left_y1,
                            foot_left_x2, foot_left_y2,
                            foot_left_x1, foot_left_y1,
                            angle_left,
                            orange)

    const foot_right_x1 = body_x + body_width - foot_width
    const foot_right_y1 = foot_y
    const foot_right_x2 = foot_right_x1 + foot_width
    const foot_right_y2 = foot_right_y1 + foot_height

    drawRotatedRectangle(image,
                            foot_right_x1, foot_right_y1,
                            foot_right_x2, foot_right_y2,
                            foot_right_x1 + foot_width, foot_right_y1,
                            angle_right,
                            orange)
}

const drawArms = (image : Image, angle_left : number, angle_right : number) => {
    const arm_left_x1 = body_x - arm_width + 1
    const arm_left_y1 = arm_y + 1
    const arm_left_x2 = arm_left_x1 + arm_width
    const arm_left_y2 = arm_left_y1 + arm_height

    const arm_center_left_x = Math.floor((arm_left_x1 + arm_left_x2) / 2)
    const arm_center_left_y = arm_left_y1

    drawRotatedEllipse(image,
                        arm_left_x1, arm_left_y1,
                        arm_left_x2, arm_left_y2,
                        arm_center_left_x, arm_center_left_y,
                        -angle_left,
                        blue)

    const arm_right_x1 = body_x + body_width - 1
    const arm_right_y1 = arm_y + 1
    const arm_right_x2 = arm_right_x1 + arm_width
    const arm_right_y2 = arm_right_y1 + arm_height

    const arm_center_right_x = Math.floor((arm_right_x1 + arm_right_x2) / 2)
    const arm_center_right_y = arm_right_y1

    drawRotatedEllipse(image,
                        arm_right_x1, arm_right_y1,
                        arm_right_x2, arm_right_y2,
                        arm_center_right_x, arm_center_right_y,
                        angle_right,
                        blue)
}

// const drawPenguin = (image : Image, angles : number[]) => {
//     drawBody(image)
//     drawHead(image, angles[4])
//     drawFeet(image, angles[2], angles[3])
//     drawArms(image, -angles[0], -angles[1])
// }

const defaultPose : AngleData = {
    ARM : {
        left: 30,
        right: 30
    },
    LEG : {
        left: 0,
        right: 0
    },
    HEAD: 0
}

const drawDefaultPenguin = (image : Image) => {
    drawBody(image)
    drawHead(image, defaultPose.HEAD, null, "neutral")
    drawFeet(image, defaultPose.LEG.left, defaultPose.LEG.right)
    drawArms(image, -defaultPose.ARM.left, -defaultPose.ARM.right)
}

const drawPenguin = (image : Image, data : LLMData, frame : number ) => {
    const angles = extractAngle(data, frame);
    drawBody(image)
    drawHead(image, angles.HEAD, data.EYE, data.FACE)
    drawFeet(image, angles.LEG.left, angles.LEG.right)
    drawArms(image, -angles.ARM.left, -angles.ARM.right)
}

export {drawPenguin, drawDefaultPenguin, penguinMeasures, framerate}