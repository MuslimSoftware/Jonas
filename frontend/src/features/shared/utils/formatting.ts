// Simple timestamp formatter using toLocaleString for better timezone handling
export const formatTimestamp = (isoString?: string): string | null => {
  if (!isoString) return null;
  
  const correctedIsoString = isoString.endsWith('Z') ? isoString : `${isoString}Z`;

  try {
    // Now parse the corrected string
    const date = new Date(correctedIsoString);
    if (isNaN(date.getTime())) return null;

    return date.toLocaleString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit', 
        hour12: true 
    });

  } catch (error) {
    console.error("Error formatting timestamp:", error);
    return null;
  }
};
  