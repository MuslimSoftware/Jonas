import React from 'react';
import {
  StyleSheet,
  Pressable,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { BaseRow, BgView, FgView } from '@/features/shared/components/layout';
import { paddings, borderRadii, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';
import { Colors } from '@/features/shared/theme/colors';
import { useChat } from '../context';

interface ChatInputProps {}

export const ChatInput: React.FC<ChatInputProps> = ({}) => {
  const { theme } = useTheme();
  const { currentMessage, setCurrentMessageText, sendMessage } = useChat(); 

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
    >
      <BgView style={styles.inputContainer}>
        <BaseRow style={styles.inputRow}> 
          <TextInput 
            style={styles.textInput}
            placeholder="Type your message..."
            placeholderTextColor={theme.colors.text.secondary}
            value={currentMessage}
            onChangeText={setCurrentMessageText}
            multiline
          />
          <FgView style={styles.sendButtonContainer}>
            <Pressable onPress={sendMessage} style={styles.sendButton}>
              <Ionicons name="send-outline" size={iconSizes.xsmall} color={Colors.gray50} />
            </Pressable>
          </FgView>
        </BaseRow>
      </BgView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  inputContainer: {
    padding: paddings.medium,
    borderRadius: borderRadii.large,
    marginBottom: Platform.select({ ios: paddings.large, android: paddings.large, web: paddings.medium }),
    marginHorizontal: paddings.medium,
  },
  inputRow: {
    alignItems: 'center',
  },
  textInput: {
    flex: 1,
    maxHeight: 100,
    marginRight: gaps.small,
    paddingVertical: paddings.small,
    paddingHorizontal: paddings.small, 
    borderRadius: borderRadii.medium,
  },
  sendButtonContainer: {
      borderRadius: borderRadii.round,
      padding: paddings.medium,
  },
  sendButton: {
  },
}); 