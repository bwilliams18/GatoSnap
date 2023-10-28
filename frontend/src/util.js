export const bitsToGB = bits => {
  return `${(bits / 1024 / 1024 / 1024).toFixed(2)} GB`;
};
