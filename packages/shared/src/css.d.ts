declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
}

// Add declarations for other CSS module types if you use them (e.g., .scss, .less)
declare module '*.module.scss' {
  const classes: { readonly [key: string]: string };
  export default classes;
} 