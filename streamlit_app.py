/<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>The Third Voice</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #2d3748;
      overflow-x: hidden;
    }

    /* Animated background particles */
    .particles {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
    }

    .particle {
      position: absolute;
      width: 4px;
      height: 4px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      animation: float 6s ease-in-out infinite;
    }

    @keyframes float {
      0%, 100% { transform: translateY(0px) rotate(0deg); }
      50% { transform: translateY(-20px) rotate(180deg); }
    }

    /* Main container */
    .container {
      position: relative;
      z-index: 1;
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 20px;
    }

    /* Header */
    header {
      text-align: center;
      padding: 80px 0 60px;
      background: rgba(255, 255, 255, 0.05);
      backdrop-filter: blur(10px);
      margin-bottom: 40px;
      border-radius: 0 0 40px 40px;
    }

    .logo {
      font-size: 3.5rem;
      font-weight: 700;
      background: linear-gradient(45deg, #fff, #f7fafc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 20px;
      text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
    }

    .tagline {
      font-size: 1.3rem;
      color: rgba(255, 255, 255, 0.9);
      font-weight: 300;
      letter-spacing: 0.5px;
    }

    /* Content sections */
    .content-section {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-radius: 20px;
      padding: 40px;
      margin: 40px 0;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .content-section:hover {
      transform: translateY(-5px);
      box-shadow: 0 30px 60px rgba(0, 0, 0, 0.15);
    }

    h2 {
      font-size: 2rem;
      font-weight: 600;
      margin-bottom: 25px;
      color: #2d3748;
      display: flex;
      align-items: center;
      gap: 15px;
    }

    .emoji {
      font-size: 2.5rem;
      filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
    }

    p {
      font-size: 1.1rem;
      line-height: 1.8;
      margin-bottom: 20px;
      color: #4a5568;
    }

    /* Quote styling */
    .quote {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      padding: 40px;
      border-radius: 20px;
      margin: 40px 0;
      position: relative;
      overflow: hidden;
    }

    .quote::before {
      content: '"';
      position: absolute;
      top: -20px;
      left: 20px;
      font-size: 8rem;
      opacity: 0.2;
      font-family: serif;
    }

    .quote p {
      font-size: 1.4rem;
      font-style: italic;
      color: rgba(255, 255, 255, 0.95);
      margin: 0;
      position: relative;
      z-index: 2;
    }

    /* Mission section */
    .mission {
      background: linear-gradient(135deg, #ff6b6b, #ee5a24);
      color: white;
    }

    .mission h2 {
      color: white;
    }

    .mission p {
      color: rgba(255, 255, 255, 0.9);
    }

    /* Features list */
    .features {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin: 30px 0;
    }

    .feature-item {
      background: rgba(102, 126, 234, 0.1);
      padding: 25px;
      border-radius: 15px;
      border-left: 4px solid #667eea;
      transition: all 0.3s ease;
    }

    .feature-item:hover {
      background: rgba(102, 126, 234, 0.2);
      transform: translateX(5px);
    }

    /* Response section */
    .response-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 25px;
      margin: 30px 0;
    }

    .response-item {
      background: linear-gradient(135deg, #f093fb, #f5576c);
      color: white;
      padding: 30px;
      border-radius: 15px;
      text-align: center;
    }

    .response-item .emoji {
      font-size: 3rem;
      margin-bottom: 15px;
      display: block;
    }

    /* CTA Button */
    .cta {
      text-align: center;
      margin: 60px 0;
    }

    .cta-button {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      padding: 20px 40px;
      border-radius: 50px;
      text-decoration: none;
      font-weight: 600;
      font-size: 1.2rem;
      display: inline-block;
      box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .cta-button::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
      transition: left 0.5s ease;
    }

    .cta-button:hover::before {
      left: 100%;
    }

    .cta-button:hover {
      transform: translateY(-3px);
      box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
    }

    .cta p {
      margin-top: 20px;
      font-size: 1rem;
      color: rgba(255, 255, 255, 0.8);
    }

    /* Footer */
    footer {
      background: rgba(0, 0, 0, 0.8);
      color: rgba(255, 255, 255, 0.9);
      padding: 60px 0;
      text-align: center;
      margin-top: 80px;
    }

    footer p {
      font-size: 1.1rem;
      line-height: 1.8;
      margin-bottom: 20px;
      color: rgba(255, 255, 255, 0.8);
    }

    .signature {
      font-size: 1.2rem;
      font-weight: 500;
      color: #667eea;
      margin-top: 30px;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .logo {
        font-size: 2.5rem;
      }
      
      .content-section {
        padding: 25px;
        margin: 20px 0;
      }
      
      h2 {
        font-size: 1.5rem;
      }
      
      .features {
        grid-template-columns: 1fr;
      }
      
      .response-grid {
        grid-template-columns: 1fr;
      }
    }

    /* Scroll animations */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(30px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .fade-in-up {
      animation: fadeInUp 0.8s ease-out;
    }
  </style>
</head>
<body>
  <!-- Animated background particles -->
  <div class="particles">
    <div class="particle" style="left: 10%; animation-delay: 0s;"></div>
    <div class="particle" style="left: 20%; animation-delay: 1s;"></div>
    <div class="particle" style="left: 30%; animation-delay: 2s;"></div>
    <div class="particle" style="left: 40%; animation-delay: 3s;"></div>
    <div class="particle" style="left: 50%; animation-delay: 4s;"></div>
    <div class="particle" style="left: 60%; animation-delay: 5s;"></div>
    <div class="particle" style="left: 70%; animation-delay: 0.5s;"></div>
    <div class="particle" style="left: 80%; animation-delay: 1.5s;"></div>
    <div class="particle" style="left: 90%; animation-delay: 2.5s;"></div>
  </div>

  <div class="container">
    <header>
      <div class="logo">🧠💬 The Third Voice</div>
      <div class="tagline">An AI Co-Mediator for Emotionally Intelligent Relationships</div>
    </header>

    <main>
      <div class="content-section fade-in-up">
        <h2><span class="emoji">👋</span> You Found Me Through My LinkedIn Story</h2>
        <div class="quote">
          <p>"When two people can't hear each other, they need a third voice — not to take sides, but to help love sound like love again."</p>
        </div>
      </div>

      <div class="content-section mission fade-in-up">
        <h2><span class="emoji">🕯️</span> This Mission Started From My Prison Cell</h2>
        <p>
          For the last 15 months, I've been using AI to fight for my family — from behind bars. Not to launch a startup. But because I was watching the most important relationship in my life crumble, one misunderstood text at a time.
        </p>
        <p>
          The AI didn't just help me communicate better. It helped me become the partner and father I wanted to be.
        </p>
        <p>
          Now I'm building <strong>The Third Voice</strong> — so every person struggling with communication can have the same chance to fight for their relationships.
        </p>
      </div>

      <div class="content-section fade-in-up">
        <h2><span class="emoji">💡</span> What You're Really Joining</h2>
        <div class="features">
          <div class="feature-item">
            <strong>✅ Real-time coaching</strong><br>
            Before you send something you'll regret
          </div>
          <div class="feature-item">
            <strong>✅ Guidance when triggered</strong><br>
            When you receive a message that sets you off
          </div>
          <div class="feature-item">
            <strong>✅ Co-parenting tools</strong><br>
            Help co-parents keep the focus on their kids
          </div>
          <div class="feature-item">
            <strong>✅ Pattern recognition</strong><br>
            Break cycles of miscommunication
          </div>
        </div>
        <p>
          But more than features, this is about <strong>hope</strong> — hope that love doesn't have to die from misunderstanding.
        </p>
      </div>

      <div class="content-section fade-in-up">
        <h2><span class="emoji">📬</span> The Response So Far</h2>
        <div class="response-grid">
          <div class="response-item">
            <span class="emoji">👩‍👧</span>
            <strong>Fighting Parents</strong><br>
            Parents in custody battles who just want to communicate for their kids
          </div>
          <div class="response-item">
            <span class="emoji">💔</span>
            <strong>Struggling Couples</strong><br>
            Couples on the brink who still love each other but can't find the words
          </div>
          <div class="response-item">
            <span class="emoji">🤝</span>
            <strong>Desperate Fighters</strong><br>
            People like me — desperate to save what matters most
          </div>
        </div>
        <p style="text-align: center; font-size: 1.2rem; font-weight: 500; margin-top: 30px;">
          Every message reminds me: <strong>This has to exist.</strong>
        </p>
      </div>

      <div class="content-section fade-in-up">
        <h2><span class="emoji">🤝</span> Help Me Build This</h2>
        <p>I'm looking for:</p>
        <div class="features">
          <div class="feature-item">
            <strong>Co-founders</strong> who share the vision
          </div>
          <div class="feature-item">
            <strong>Beta testers</strong> willing to give feedback
          </div>
          <div class="feature-item">
            <strong>Advisors</strong> with experience in tech, law, psychology, or conflict resolution
          </div>
          <div class="feature-item">
            <strong>Believers</strong> who know this is bigger than profit
          </div>
        </div>
      </div>

      <div class="cta fade-in-up">
        <a href="mailto:TheThirdVoice.ai@gmail.com" class="cta-button">📩 Send Me a Message</a>
        <p>Tell me your story. Tell me how you want to help. Tell me what this could mean for your relationships.</p>
      </div>
    </main>

    <footer>
      <p>
        I'm building <strong>The Third Voice</strong> from a place where I've lost almost everything — except hope.<br/>
        Because if AI can help me fight for my family from here, it can help anyone fight for theirs from anywhere.
      </p>
      <p>
        My pain doesn't have to be for nothing. Your relationship doesn't have to be another casualty of miscommunication.
      </p>
      <div class="signature">
        — Predrag Mirkovic<br/>
        Founder, The Third Voice<br/>
        Fighting for families, one message at a time.
      </div>
    </footer>
  </div>

  <script>
    // Add scroll animations
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.animation = 'fadeInUp 0.8s ease-out';
        }
      });
    }, observerOptions);

    document.querySelectorAll('.content-section').forEach(section => {
      observer.observe(section);
    });

    // Add floating particles animation
    const particles = document.querySelectorAll('.particle');
    particles.forEach(particle => {
      const randomDelay = Math.random() * 6;
      const randomDuration = 4 + Math.random() * 4;
      particle.style.animationDelay = randomDelay + 's';
      particle.style.animationDuration = randomDuration + 's';
      particle.style.top = Math.random() * 100 + '%';
    });
  </script>
</body>
  </html>
