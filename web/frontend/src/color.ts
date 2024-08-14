type Color = {
    r: number,
    g: number,
    b: number,
    a: number
};

const newColor = (r: number, g: number, b: number) => {
    return <Color> {
        r: r,
        g: g,
        b: b,
        a: 255
    };
}

const toString = (color: Color) => {
    return `(${color.r},${color.g},${color.b})`
}

const blue = newColor(0, 0, 255);
const white = newColor(255, 255, 255);
const orange = newColor(255, 125, 0)
const yellow = newColor(255, 222, 40);
const red = newColor(255, 0, 0);
const bright = newColor(200, 200, 200);

export type { Color }
export { red, bright, blue, white, orange, yellow, toString, newColor }