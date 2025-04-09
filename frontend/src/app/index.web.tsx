import { Redirect } from 'expo-router';

export default function WebIndex() {
  // Redirect web users directly to the chat screen
  return <Redirect href="/(main)/chat" />;
} 