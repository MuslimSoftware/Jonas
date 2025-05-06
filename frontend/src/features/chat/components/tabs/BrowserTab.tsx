import React from 'react';
import {
  StyleSheet,
  Pressable,
  Image,
  View,
  ActivityIndicator,
  Text,
} from 'react-native';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Theme } from '@/features/shared/context/ThemeContext';
import { ScreenshotControls } from '../common/ScreenshotControls'; // Adjusted import path
import { ScreenshotData } from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { FgView } from '@/features/shared/components/layout';
import { TextBody, TextCaption } from '@/features/shared/components/text';

interface BrowserTabProps {
  screenshots: ScreenshotData[];
  screenshotsError: ApiError | null;
  loadingScreenshots: boolean;
  totalScreenshotsCount: number | null;
  currentScreenshotIndex: number;
  loadingMoreScreenshots: boolean;
  hasMoreScreenshots: boolean;
  fetchMoreScreenshots: () => void;
  openImageModal: (uri: string) => void;
  setCurrentScreenshotIndex: React.Dispatch<React.SetStateAction<number>>;
  justLoadedMoreRef: React.MutableRefObject<boolean>;
}

export const BrowserTab: React.FC<BrowserTabProps> = ({
  screenshots,
  screenshotsError,
  loadingScreenshots,
  totalScreenshotsCount,
  currentScreenshotIndex,
  loadingMoreScreenshots,
  hasMoreScreenshots,
  fetchMoreScreenshots,
  openImageModal,
  setCurrentScreenshotIndex,
  justLoadedMoreRef,
}) => {
  const { theme } = useTheme();
  const styles = getStyles(theme);

  return (
    <View style={styles.tabContentContainer}>
      {screenshotsError ? (
        <Text style={styles.errorText}>Error loading screenshots.</Text>
      ) : totalScreenshotsCount !== null && totalScreenshotsCount > 0 ? (
        <View style={styles.carouselContainer}>
          <Pressable
            style={styles.screenshotImageWrapper}
            onPress={() =>
              screenshots[currentScreenshotIndex]?.image_data &&
              openImageModal(screenshots[currentScreenshotIndex].image_data)
            }
            disabled={!screenshots[currentScreenshotIndex]?.image_data}
          >
            {loadingMoreScreenshots || !screenshots[currentScreenshotIndex] ? (
              <View style={styles.screenshotImage}>
                <ActivityIndicator color={theme.colors.text.primary} />
              </View>
            ) : (
              <Image
                source={{ uri: screenshots[currentScreenshotIndex].image_data }}
                style={styles.screenshotImage}
                resizeMode="contain"
              />
            )}
          </Pressable>
          {screenshots[currentScreenshotIndex] && 
              <View style={styles.detailsCard}>
              <TextBody style={styles.statusText}>
                {screenshots[currentScreenshotIndex]?.memory ?? 'Status N/A'}
              </TextBody>
          
              <TextCaption style={styles.nextStepText}>
                Next step&nbsp;· {screenshots[currentScreenshotIndex]?.next_goal ?? 'N/A'}
              </TextCaption>
            </View>
          }
          <ScreenshotControls
            currentIndex={currentScreenshotIndex}
            totalLoaded={screenshots.length}
            totalCount={totalScreenshotsCount}
            isLoadingMore={loadingMoreScreenshots}
            onGoBack={() => {
              // NOTE: Logic seems reversed (Back goes forward, Forward goes back)
              // Keeping original logic for now, but consider reviewing this.
              if (
                currentScreenshotIndex === screenshots.length - 1 &&
                hasMoreScreenshots
              ) {
                justLoadedMoreRef.current = true;
                fetchMoreScreenshots();
              } else if (currentScreenshotIndex < screenshots.length - 1) {
                setCurrentScreenshotIndex((prev) => prev + 1);
              }
            }}
            onGoForward={() =>
              setCurrentScreenshotIndex((prev) => Math.max(0, prev - 1))
            }
          />
        </View>
      ) : loadingScreenshots ? (
        // Show loading indicator during initial load
        <ActivityIndicator color={theme.colors.text.primary} />
      ) : (
        // Show empty text only if not loading and count is 0 or null
        <Text style={styles.emptyText}>No agent screenshots available.</Text>
      )}
    </View>
  );
};

const getStyles = (theme: Theme) =>
  StyleSheet.create({
    /* layout */
    tabContentContainer: {
      flex: 1,
      alignItems: 'center',
      paddingVertical: paddings.medium,
    },
    carouselContainer: {
      width: '100%',
      alignItems: 'center',
      justifyContent: 'center',
    },

    /* screenshot */
    screenshotImageWrapper: {
      width: '100%',
      backgroundColor: theme.colors.layout.foreground,
      marginBottom: paddings.medium,
    },
    screenshotImage: {
      width: '100%',
      aspectRatio: 1280 / 1100,
    },

    /* details card */
    detailsCard: {
      width: '100%',
      padding: paddings.medium,
      marginTop: paddings.medium,
      borderRadius: borderRadii.large,
      backgroundColor: theme.colors.layout.foreground,
      gap: paddings.xsmall,

      /* soft shadow / elevation */
      shadowColor: '#000',
      shadowOpacity: 0.05,
      shadowRadius: 10,
      shadowOffset: { width: 0, height: 4 },
      elevation: 3,
    },

    /* typography */
    statusText: {
      fontWeight: '600',
      fontSize: theme.typography.body1.fontSize * 1.1,
      color: theme.colors.text.primary,
    },
    nextStepText: {
      color: theme.colors.text.secondary,
      marginTop: paddings.xxsmall,
    },

    /* misc */
    errorText: {
      color: theme.colors.indicators.error,
      textAlign: 'center',
    },
    emptyText: {
      color: theme.colors.text.secondary,
      textAlign: 'center',
    },
  });