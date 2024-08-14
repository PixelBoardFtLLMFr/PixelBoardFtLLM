import angry from './assets/effects/angry.png';
import cloud from './assets/effects/cloud.png';
import heart from './assets/effects/heart.png';
import sleepy from './assets/effects/sleepy.png';
import spark from './assets/effects/spark.png';
import sweat from './assets/effects/sweat.png';

import { Image, loadImageFromPng, pasteImage } from './image';
import { penguinMeasures } from './penguin';

let particles: Record<string, Image> = {};
let particlesLoaded: Promise<void>;

const particlesLocation: Record<string, number[]> = {
    "angry": [penguinMeasures.head_x, penguinMeasures.head_y], 
    "heart": [penguinMeasures.body_x, penguinMeasures.body_y], 
    "spark": [penguinMeasures.head_x + penguinMeasures.head_size, penguinMeasures.head_y], 
    "sleepy": [0, penguinMeasures.head_y], 
    "sweat": [penguinMeasures.head_x + penguinMeasures.head_size, penguinMeasures.head_y], 
    "cloud": [0, 0], 
}

const loadParticles = () => {
  const paths: Record<string, string> = {
    "angry": angry,
    "heart": heart,
    "spark": spark,
    "sleepy": sleepy,
    "sweat": sweat,
    "cloud": cloud,
  };

  const loadPromises = Object.keys(paths).map((key) => {
    const path = paths[key];
    return loadImageFromPng(path).then((image) => {
      particles[key] = image;
    });
  });

  particlesLoaded = Promise.all(loadPromises).then(() => {
    console.log("All particles loaded");
  });
};

const addSpecialEffect = async (penguin: Image, effect: string) => {
  if (!particlesLoaded) {
    console.log("Particles not loaded");
    return;
  }

  await particlesLoaded;

  const effectImage = particles[effect];
  if (!effectImage) return;

  pasteImage(effectImage, penguin, particlesLocation[effect][0], particlesLocation[effect][1]);
};

export { addSpecialEffect, loadParticles };