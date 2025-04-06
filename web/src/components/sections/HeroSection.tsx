import React from 'react';
import styles from './HeroSection.module.css';
import Button from '@/components/shared/Button';
import { BRAND_NAME } from '@uniskit/shared';

const heroData = {
  headlineMain: `Build Fast. Launch Faster.`,
  headlineHighlight: "Launch Faster.",
  headlineSub: `No More Boilerplate.`,
  description: `${BRAND_NAME} provides a production-ready full-stack monorepo foundation.
   Launch your next business without wasting time writing boilerplate.`,
  cta: {
    text: "Get Started",
    href: "#value-props",
  },
};

const commandLines = [
  "# 1. Clone the repository",
  "git clone git@github.com:MuslimSoftware/UnisKit.git",
  "cd UnisKit",
  "",
  "# 2. Start Backend & Redis (Docker)",
  "docker-compose up -d",
  "",
  "# 3. Run the Mobile App (React Native/Expo)",
  "cd mobile",
  "npm install",
  "npm run start:dev",
  "",
  "# 4. Run the Web App (React/Vite)",
  "cd web",
  "npm install",
  "npm run dev",
];

const HeroSection = () => {
  const renderHeadline = () => {
    const parts = heroData.headlineMain.split(heroData.headlineHighlight);
    if (parts.length === 2) {
      return (
        <>
          {parts[0]}<span className={styles.headlineHighlight}>{heroData.headlineHighlight}</span>{parts[1]}
        </>
      );
    }
    return <>{heroData.headlineMain}</>;
  };

  const renderCodeSnippet = () => {
    const keywords = ["git", "cd", "npm"];
    const keywordRegex = /(\b(?:git|cd|npm)\b)/g;
    const targetGitLink = "git@github.com:MuslimSoftware/UnisKit.git";

    const processSubstring = (text: string, keyPrefix: string): (string | JSX.Element)[] => {
      if (!text) return [];
      const parts = text.split(keywordRegex).filter(part => part);
      return parts.map((part, index) =>
        keywords.includes(part) ? (
          <span key={`${keyPrefix}-${index}`} className={styles.keyword}>{part}</span>
        ) : (
          part
        )
      );
    };

    return commandLines.map((line, index) => {
      if (line.trim().startsWith("#")) {
        const commentText = line.slice(line.indexOf('#'));
        return <React.Fragment key={index}><span className={styles.comment}>{commentText}</span><br /></React.Fragment>;
      } else if (line.trim() === "") {
        return <br key={index} />;
      } else {
        const linkIndex = line.indexOf(targetGitLink);
        let elements: (string | JSX.Element)[] = [];

        if (linkIndex !== -1) {
          const before = line.substring(0, linkIndex);
          const after = line.substring(linkIndex + targetGitLink.length);

          elements = [
            ...processSubstring(before, `line-${index}-before`),
            <span key={`line-${index}-link`} className={styles.gitLink}>{targetGitLink}</span>,
            ...processSubstring(after, `line-${index}-after`)
          ];
        } else {
          elements = processSubstring(line, `line-${index}-full`);
        }

        return (
          <React.Fragment key={index}>
            {elements}
            <br />
          </React.Fragment>
        );
      }
    });
  };

  return (
    <section className={styles.hero}>
      <div className={styles.content}>
        <h1 className={styles.headline}>
          {renderHeadline()}
          <span className={styles.headlineSub}>{heroData.headlineSub}</span>
        </h1>

        <p className={styles.description}>{heroData.description}</p>

        <div className={styles.ctaContainer}>
          <a href={heroData.cta.href} className={styles.ctaLink}>
            <Button
              variant="primary"
              className={styles.ctaButton}
            >
              {heroData.cta.text}
            </Button>
          </a>
        </div>

        <div className={styles.visualPlaceholder}>
          <div className={styles.codeSnippet}>
            <pre><code>
              {renderCodeSnippet()}
            </code></pre>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection; 