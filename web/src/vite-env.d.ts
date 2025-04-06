// Allows TypeScript to understand imports of CSS Modules
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
} 