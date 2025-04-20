import React, { useEffect, useState, useRef } from 'react';
import { StyleSheet, Pressable, ScrollView, Image, View, Dimensions, ActivityIndicator, Text } from 'react-native';
import { BgView, BaseColumn } from '@/features/shared/components/layout';
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../../context';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';
import Animated, { 
  useSharedValue, 
  useAnimatedStyle, 
  withTiming, 
  Easing 
} from 'react-native-reanimated';
import { Theme } from '@/features/shared/context/ThemeContext';
import ScreenshotModal from '../modals/ScreenshotModal';

type Tab = 'browser' | 'context';

interface RightChatPanelProps {
  isVisible: boolean;
  onClose: () => void;
}

const PANEL_WIDTH_PERCENT = 30;
const ANIMATION_DURATION = 250;

export const RightChatPanel: React.FC<RightChatPanelProps> = ({
  isVisible,
  onClose,
}) => {
  const { theme } = useTheme();
  const { 
    screenshots, 
    loadingScreenshots, 
    screenshotsError, 
    fetchScreenshots, 
    selectedChatId,
    fetchMoreScreenshots,
    hasMoreScreenshots,
    loadingMoreScreenshots,
    totalScreenshotsCount,
  } = useChat();
  const animatedWidth = useSharedValue(isVisible ? PANEL_WIDTH_PERCENT : 0);
  const [activeTab, setActiveTab] = useState<Tab>('browser');
  const [currentScreenshotIndex, setCurrentScreenshotIndex] = useState(0);
  const justLoadedMoreRef = useRef(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalImageUri, setModalImageUri] = useState<string | null>(null);

  const openImageModal = (uri: string) => {
    setModalImageUri(uri);
    setIsModalVisible(true);
  };

  const closeImageModal = () => {
    setIsModalVisible(false);
    setModalImageUri(null);
  };

  useEffect(() => {
    animatedWidth.value = withTiming(
      isVisible ? PANEL_WIDTH_PERCENT : 0,
      { duration: ANIMATION_DURATION, easing: Easing.inOut(Easing.ease) }
    );
    if (isVisible && selectedChatId) {
      fetchScreenshots(selectedChatId);
    }
  }, [isVisible, animatedWidth, selectedChatId, fetchScreenshots]);

  useEffect(() => {
    if (justLoadedMoreRef.current) {
      setCurrentScreenshotIndex(prev => Math.min(prev + 1, screenshots.length - 1));
      justLoadedMoreRef.current = false;
    }
  }, [screenshots]);

  const animatedStyle = useAnimatedStyle(() => {
    const marginRightValue = isVisible ? paddings.medium : 0;
    return {
      width: `${animatedWidth.value}%`,
      marginRight: withTiming(marginRightValue, { duration: ANIMATION_DURATION, easing: Easing.inOut(Easing.ease) }),
      overflow: 'hidden',
    };
  });

  if (!isVisible && animatedWidth.value === 0) {
     return null;
  }

  const styles = getStyles(theme);

  return (
    <Animated.View style={[styles.animatedContainer, animatedStyle]}>
      <BgView style={styles.rightPanelContent}>
        <Pressable style={styles.closeRightPanelButton} onPress={onClose}>
          <Ionicons name="close-outline" size={iconSizes.medium} color={theme.colors.text.secondary} />
        </Pressable>

        <View style={styles.tabContainer}>
          <Pressable 
            style={[styles.tabButton, activeTab === 'browser' && styles.activeTabButton]}
            onPress={() => setActiveTab('browser')}
          >
            <Text style={[styles.tabText, activeTab === 'browser' && styles.activeTabText]}>Browser</Text>
          </Pressable>
          <Pressable 
            style={[styles.tabButton, activeTab === 'context' && styles.activeTabButton]}
            onPress={() => setActiveTab('context')}
          >
            <Text style={[styles.tabText, activeTab === 'context' && styles.activeTabText]}>Context</Text>
          </Pressable>
        </View>

        <BaseColumn style={styles.panelColumn}>
          {activeTab === 'browser' ? (
            <View style={styles.tabContentContainer}>
              {loadingScreenshots ? <ActivityIndicator color={theme.colors.text.primary} /> : null}
              {screenshotsError ? <Text style={styles.errorText}>Error loading screenshots.</Text> : null}
              
              {(!loadingScreenshots && !screenshotsError) ? (
                totalScreenshotsCount !== null && totalScreenshotsCount > 0 ? (
                  <View style={styles.carouselContainer}>
                    <Pressable style={styles.screenshotImage} onPress={() => openImageModal(screenshots[currentScreenshotIndex].image_data)}>
                      <Image 
                        source={{ uri: screenshots[currentScreenshotIndex].image_data }}
                        style={styles.screenshotImage}
                        resizeMode="contain"
                      />
                    </Pressable>
                    <View style={styles.controlContainer}>
                      <Pressable 
                        style={styles.arrowButton} 
                        onPress={() => {
                          if (currentScreenshotIndex === screenshots.length - 1 && hasMoreScreenshots) {
                            justLoadedMoreRef.current = true;
                            fetchMoreScreenshots();
                          } else if (currentScreenshotIndex < screenshots.length - 1) {
                             setCurrentScreenshotIndex(prev => prev + 1);
                          }
                        }}
                        disabled={(totalScreenshotsCount !== null && (totalScreenshotsCount - currentScreenshotIndex) === 1) || loadingMoreScreenshots}
                      >
                        <Ionicons name="chevron-back-outline" size={iconSizes.large} color={(totalScreenshotsCount !== null && (totalScreenshotsCount - currentScreenshotIndex) === 1) || loadingMoreScreenshots ? theme.colors.text.disabled : theme.colors.text.primary} />
                      </Pressable>

                      <View style={styles.indexIndicator}>
                        <Text style={styles.indexText}>
                          {totalScreenshotsCount !== null ? `${totalScreenshotsCount - currentScreenshotIndex} / ${totalScreenshotsCount}` : '? / ?'}
                        </Text>
                      </View>

                      <Pressable 
                        style={styles.arrowButton} 
                        onPress={() => setCurrentScreenshotIndex(prev => Math.max(0, prev - 1))}
                        disabled={currentScreenshotIndex === 0}
                      >
                        <Ionicons name="chevron-forward-outline" size={iconSizes.large} color={currentScreenshotIndex === 0 ? theme.colors.text.disabled : theme.colors.text.primary} />
                      </Pressable>
                    </View>
                  </View>
                ) : loadingScreenshots ? (
                  null
                ) : (
                  <Text style={styles.emptyText}>No agent screenshots available.</Text>
                )
              ) : null}
            </View>
          ) : null}

          {activeTab === 'context' ? (
            <View style={styles.tabContentContainer}>
              <Text style={styles.contextPlaceholder}>Context View Placeholder</Text>
            </View>
          ) : null}
        </BaseColumn>
        
        <ScreenshotModal 
          isVisible={isModalVisible} 
          screenshots={screenshots} 
          onClose={closeImageModal} 
          currentIndex={currentScreenshotIndex}
          totalLoaded={screenshots.length}
          totalCount={totalScreenshotsCount}
          onGoBack={() => {
            if (currentScreenshotIndex === screenshots.length - 1 && hasMoreScreenshots) {
              justLoadedMoreRef.current = true; 
              fetchMoreScreenshots();
            } else if (currentScreenshotIndex < screenshots.length - 1) {
               setCurrentScreenshotIndex(prev => prev + 1);
            }
          }}
          onGoForward={() => setCurrentScreenshotIndex(prev => Math.max(0, prev - 1))}
          loadingMoreScreenshots={loadingMoreScreenshots}
        />
      </BgView>
    </Animated.View>
  );
};

const getStyles = (theme: Theme) => StyleSheet.create({
  animatedContainer: {
    height: '97.5%',
    borderRadius: borderRadii.large,
    overflow: 'hidden',
  },
  rightPanelContent: {
    height: '100%',
    position: 'relative',
    flexDirection: 'column',
  },
  closeRightPanelButton: {
    position: 'absolute',
    top: paddings.medium, 
    right: paddings.medium, 
    zIndex: 1,
  },
  panelColumn: {
    flex: 1,
    paddingTop: paddings.medium,
    paddingHorizontal: paddings.medium,
  },
  tabContainer: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.layout.border,
    paddingHorizontal: paddings.medium, 
    paddingTop: paddings.xlarge,
  },
  tabButton: {
    paddingVertical: paddings.small,
    paddingHorizontal: paddings.medium,
    marginRight: paddings.small,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTabButton: {
    borderBottomColor: theme.colors.text.primary,
  },
  tabText: {
    color: theme.colors.text.secondary,
    fontWeight: '500',
  },
  activeTabText: {
    color: theme.colors.text.primary,
    fontWeight: '600',
  },
  tabContentContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  carouselContainer: {
    width: '100%',
    height: 450,
    justifyContent: 'center',
    alignItems: 'center',
  },
  arrowButton: {
    opacity: 1,
  },
  indexIndicator: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: paddings.small,
    paddingVertical: 2,
    borderRadius: borderRadii.small,
    minWidth: 50,
    alignItems: 'center',
    marginHorizontal: paddings.medium,
  },
  indexText: {
    color: '#fff',
    fontSize: 12,
  },
  screenshotImage: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.layout.foreground,
    height: 350,
    width: '100%'
  },
  controlContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    paddingHorizontal: paddings.large,
    marginTop: paddings.small,
  },
  contextPlaceholder: {
    color: theme.colors.text.secondary,
    fontSize: 16,
  },
  errorText: {
    color: theme.colors.indicators.error,
    marginTop: paddings.medium,
  },
  emptyText: {
    color: theme.colors.text.secondary,
    marginTop: paddings.medium,
  },
}); 