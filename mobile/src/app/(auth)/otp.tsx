import React, { useEffect, useState, useRef } from 'react'
import { StyleSheet, View, TouchableOpacity } from 'react-native'
import { AuthScreenLayout } from '@/features/auth/components/AuthScreenLayout'
import { useOTPVerification } from '@/features/auth/hooks/useOTPVerification'
import { OtpInput } from '@/features/auth/components/OtpInput'
import { TextCaption, TextLink } from '@/shared/components/text'
import { MediumColumn, SmallRow } from '@/shared/components/layout'

export default function OTPScreen() {
  const {
    otp,
    setOtp,
    loading,
    errorMessage,
    handleVerify,
    handleResendOTP,
    resendCooldown,
  } = useOTPVerification()

  const DIGIT_COUNT = 6

  // Automatically verify when the user enters the full OTP
  useEffect(() => {
    if (otp.length !== DIGIT_COUNT) {
      return;
    }

    handleVerify();
  }, [otp, handleVerify, DIGIT_COUNT]);

  return (
    <AuthScreenLayout
      title="Verify Your Email"
      subtitle="Enter the 6-digit code we sent to your email"
      buttonText={loading ? 'Verifying...' : 'Verify'}
      onButtonPress={handleVerify}
      buttonDisabled={otp.length !== DIGIT_COUNT || loading || !!errorMessage}
    >
      <MediumColumn style={styles.container}>
        <View style={styles.inputContainer}>
          <OtpInput
            value={otp}
            onChangeText={setOtp}
            digitCount={DIGIT_COUNT}
            error={!!errorMessage}
            errorMessage={errorMessage}
          />
        </View>

        <SmallRow style={styles.footerRow}>
          <TextCaption>Didn't receive the code? </TextCaption>
          <TouchableOpacity
            onPress={resendCooldown > 0 ? undefined : handleResendOTP}
            disabled={resendCooldown > 0 || loading}
            style={{ opacity: loading || resendCooldown > 0 ? 0.5 : 1 }}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <TextLink>
              {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend'}
            </TextLink>
          </TouchableOpacity>
        </SmallRow>
      </MediumColumn>
    </AuthScreenLayout>
  )
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
    alignItems: 'center',
  },
  inputContainer: {
    width: '100%',
  },
  footerRow: {
    justifyContent: 'flex-start',
    width: '100%',
  },
})
