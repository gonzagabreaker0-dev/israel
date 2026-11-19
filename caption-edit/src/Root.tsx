import React from 'react';
import {Composition} from 'remotion';
import {Edit} from './Edit';
export const FPS = 30;
export const DURATION = 2836; // 94.53s * 30
export const Root: React.FC = () => (
  <Composition id="Edit" component={Edit} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
);
