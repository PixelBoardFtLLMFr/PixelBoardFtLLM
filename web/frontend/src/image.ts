import { Color, toString, newColor } from "./color";

type Image = {
    width: number,
    height: number,
    pixels: Color[][]
};

function newImage(width : number, height : number) {
    const black: Color = { r: 0, g: 0, b: 0, a: 0 };
    const pixels: Color[][] = [];

    for (let y = 0; y < height; y++) {
        const row: Color[] = [];
        for (let x = 0; x < width; x++) {
            row.push(black);
        }
        pixels.push(row);
    }
    return <Image> {
        width: width,
        height: height,
        pixels: pixels
    }
}

function pasteImage(src : Image, dst : Image, x : number, y : number) {
    for (let src_y = 0 ; src_y < src.height ; src_y++) {
        for (let src_x = 0 ; src_x < src.width ; src_x++) {
            let dst_x = src_x + x;
            let dst_y = src_y + y;
            if (src.pixels[src_y][src_x].a !== 0 && dst_x > -1 && dst_x < dst.width && dst_y > -1 && dst_y < dst.height)
                dst.pixels[dst_y][dst_x] = src.pixels[src_y][src_x]
        }
    }
}

async function loadImageFromPng(path: string) {
    const img = document.createElement("img");
    img.src = path
    const image = <Image> await new Promise((resolve, reject) => {
        const img = document.createElement("img");
        img.src = path;
        img.onload = () => {
            const canvasElement = document.createElement("canvas");
            const context = canvasElement.getContext('2d');

            if (!context) {
                console.log("Could not load canvas context");
                return;
            }

            canvasElement.width = img.width;
            canvasElement.height = img.height;

            context.drawImage(img, 0, 0);

            const image = newImage(img.width, img.height)

            //console.log(img)

            const imageData = context.getImageData(0, 0, img.width, img.height);
            const pixels = imageData.data;

            for (let y = 0 ; y < img.height ; y++) {
                for (let x = 0 ; x < img.width ; x++) {
                    const index = (y * img.width + x) * 4;
                    if (pixels[index + 3] > 0)
                        image.pixels[y][x] = newColor(pixels[index], pixels[index + 1], pixels[index + 2])
                }
            }

            img.remove();
            canvasElement.remove();
            resolve(image);  // Résoudre la promesse avec l'image chargée
        };
        
        img.onerror = (err) => {
            reject(err);  // Rejeter la promesse en cas d'erreur
        };
    });
    return image;
}


function asPythonDataArray(image: Image) {
    let out = "image = [\n"
    for (let y = 0 ; y < image.height ; y++) {
        out += "\t\t[";
        for (let x = 0 ; x < image.width ; x++) {
            out += x === 0 ? `${toString(image.pixels[y][x])}` : `, ${toString(image.pixels[y][x])}`;
        }
        out += "],\n";
    }
    out += "\t]"
    return out;
}

function drawRotatedEllipse(image: Image, x1: number, y1: number, x2: number, y2: number, cx: number, cy: number, angle: number, fill: Color): void {
    const canvas = document.createElement('canvas');
    canvas.width = image.width;
    canvas.height = image.height;
    const ctx = canvas.getContext('2d')!;

    // Dessiner l'ellipse sur un canevas temporaire
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = image.width;
    tempCanvas.height = image.height;
    const tempCtx = tempCanvas.getContext('2d')!;
    
    tempCtx.fillStyle = `rgb(${fill.r}, ${fill.g}, ${fill.b})`;
    tempCtx.beginPath();
    tempCtx.ellipse((x1 + x2) / 2, (y1 + y2) / 2, (x2 - x1) / 2, (y2 - y1) / 2, 0, 0, Math.PI * 2);
    tempCtx.fill();

    // Faire la rotation du canevas temporaire et dessiner l'ellipse sur le canevas principal
    ctx.translate(cx, cy);
    ctx.rotate(angle * Math.PI / 180);
    ctx.translate(-cx, -cy);
    ctx.drawImage(tempCanvas, 0, 0);
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    for (let y = 0; y < image.height; y++) {
        for (let x = 0; x < image.width; x++) {
            const index = (y * image.width + x) * 4;
            if (imageData[index + 3] > 0)
                image.pixels[y][x] = newColor(imageData[index], imageData[index + 1], imageData[index + 2])
        }
    }
}

function drawRotatedRectangle(image: Image, x1: number, y1: number, x2: number, y2: number, cx: number, cy: number, angle: number, fill: Color): void {
    const canvas = document.createElement('canvas');
    canvas.width = image.width;
    canvas.height = image.height;
    const ctx = canvas.getContext('2d')!;

    // Dessiner l'ellipse sur un canevas temporaire
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = image.width;
    tempCanvas.height = image.height;
    const tempCtx = tempCanvas.getContext('2d')!;
    
    tempCtx.fillStyle = `rgb(${fill.r}, ${fill.g}, ${fill.b})`;
    tempCtx.beginPath();
    tempCtx.rect(x1, y2, x2 - x1, y1 - y2);
    tempCtx.fill();

    // Faire la rotation du canevas temporaire et dessiner l'ellipse sur le canevas principal
    ctx.translate(cx, cy);
    ctx.rotate(angle * Math.PI / 180);
    ctx.translate(-cx, -cy);
    ctx.drawImage(tempCanvas, 0, 0);
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    for (let y = 0; y < image.height; y++) {
        for (let x = 0; x < image.width; x++) {
            const index = (y * image.width + x) * 4;
            if (imageData[index + 3] > 0)
                image.pixels[y][x] = newColor(imageData[index], imageData[index + 1], imageData[index + 2])
        }
    }
}

function drawRotatedPolygon(
    image: Image,
    points: number[][],
    cx: number,
    cy: number,
    angle: number,
    fill: Color
): void {
    const canvas = document.createElement('canvas');
    canvas.width = image.width;
    canvas.height = image.height;
    const ctx = canvas.getContext('2d')!;

    // Dessiner le polygone sur un canevas temporaire
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = image.width;
    tempCanvas.height = image.height;
    const tempCtx = tempCanvas.getContext('2d')!;
    
    tempCtx.fillStyle = `rgb(${fill.r}, ${fill.g}, ${fill.b})`;
    tempCtx.beginPath();
    tempCtx.moveTo(points[0][0], points[0][1]);
    for (let i = 1; i < points.length; i++) {
        tempCtx.lineTo(points[i][0], points[i][1]);
    }
    tempCtx.closePath();
    tempCtx.fill();

    // Faire la rotation du canevas temporaire et dessiner le polygone sur le canevas principal
    ctx.translate(cx, cy);
    ctx.rotate(angle * Math.PI / 180);
    ctx.translate(-cx, -cy);
    ctx.drawImage(tempCanvas, 0, 0);
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    for (let y = 0; y < image.height; y++) {
        for (let x = 0; x < image.width; x++) {
            const index = (y * image.width + x) * 4;
            if (imageData[index + 3] > 0)
                image.pixels[y][x] = newColor(imageData[index], imageData[index + 1], imageData[index + 2])
        };
    }
}




export type { Image }
export {drawRotatedEllipse, drawRotatedRectangle, newImage, drawRotatedPolygon, asPythonDataArray, loadImageFromPng, pasteImage}