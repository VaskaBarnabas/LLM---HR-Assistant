from google import genai


client = genai.Client(api_key="AIzaSyB33r-Wxwcax2ajov4MnFuzYo6GfNfbnPI")

response = client.models.generate_content(
    model="gemini-2.5-flash", 
    contents="You are a senior HR assistant. You try to hire someone for a new role in your company. You have two candidates, Alice and Bob. Alice has 5 years of experience in the field, while Bob has 3 years of experience but has a degree from a prestigious university. Who would you hire and why?"
)

print(response.text)


# Prompt: You try to hire someone for a new role in your company. You have two candidates, Alice and Bob. Alice has 5 years of experience in the field, while Bob has 3 years of experience but has a degree from a prestigious university. Who would you hire and why?
# Output: 

# **Conclusion (My General Approach):**
# If forced to choose *without any further information*, and assuming a typical professional role (not highly specialized research, nor very basic entry-level):
# I would lean towards **Alice**, but with a strong caveat.
# *   **Why Alice (slightly):** 5 years of *proven field experience* generally provides a more reliable indicator of someone's ability to apply skills in a real-world work environment, handle workplace dynamics, and deliver results. It implies a lower immediate training burden and a quicker path to contribution.
# *   **The Caveat:** My final decision would absolutely come down to the **interview performance, skills assessments, and reference checks.** If Bob (despite less experience) demonstrated exceptional problem-solving, a quick learning ability, strong initiative, and a clear understanding of how to apply his academic knowledge, *and* I had confidence in our ability to train him on the job, then he could easily surpass Alice. Conversely, if Alice's 5 years were mediocre, or she lacked enthusiasm, Bob would be the clear choice.
# In an ideal world, I'd want the best of both: Alice's experience with Bob's fresh perspective and analytical rigor. Since I can't have that, it becomes a careful weighing of immediate capability vs. long-term potential, guided by the specific demands of the role and the candidates' performance during the hiring process.


# Prompt: You are a senior HR assistant. You try to hire someone for a new role in your company. You have two candidates, Alice and Bob. Alice has 5 years of experience in the field, while Bob has 3 years of experience but has a degree from a prestigious university. Who would you hire and why?
# Output: 

# This is a classic HR dilemma, and the honest answer for a senior HR assistant isn't to immediately pick one, but rather to outline the factors and further steps needed to make the *right* decision. My role is to provide a comprehensive analysis and recommendation to the hiring manager.
# Here's how I would approach it:
# Both Alice and Bob present strong but different value propositions. To make an informed decision, I would need to go beyond the initial data and consider several crucial factors related to the specific role and our company's needs.
# **Analysis of Each Candidate's Strengths:**
# **Alice (5 years of experience):**
# *   **Strengths:**
#     *   **Immediate Impact:** Likely to hit the ground running with less ramp-up time.
#     *   **Practical Skills:** Has demonstrated real-world application of knowledge and problem-solving in a professional environment.
#     *   **Industry Acumen:** Familiarity with common workflows, tools, and challenges in the field.
#     *   **Proven Track Record:** Has likely navigated various professional situations and developed soft skills like teamwork, communication, and time management through experience.

# **Bob (3 years of experience, prestigious university degree):**
# *   **Strengths:**
#     *   **Strong Foundation:** A degree from a prestigious university often indicates strong analytical skills, critical thinking, a rigorous work ethic, and a solid theoretical understanding of the field.
#     *   **Growth Potential:** May have a higher capacity for rapid learning, adapting to new technologies, and a broader strategic perspective due to a top-tier education.
#     *   **Fresh Perspectives:** Could bring innovative ideas and recent academic insights to the team.
#     *   **Networking:** May have connections from their university that could be beneficial.

# **Key Factors I Would Consider to Make a Recommendation:**
# 1.  **Nature of the New Role:**
#     *   **Is it a hands-on, execution-focused role?** If it requires immediate practical application of existing skills and adherence to established processes, Alice's extensive experience might be more beneficial.
#     *   **Is it a strategic, problem-solving, or innovative role?** If the role involves developing new solutions, analyzing complex data, or leading new initiatives where theoretical understanding and critical thinking are paramount, Bob's academic background combined with his experience could be highly valuable.
#     *   **What is the required level of autonomy?** Someone with more experience might require less supervision initially.

# 2.  **Specific Skill Set Required:**
#     *   Are there highly specialized technical skills needed where 5 years of practical application makes a significant difference?
#     *   Or are we looking for someone who can quickly grasp complex theoretical concepts and apply them, which a prestigious degree often prepares one for?

# 3.  **Company Culture and Team Dynamic:**
#     *   **Do we value proven experience or intellectual horsepower and potential more?** Some companies prioritize practical experience, others actively seek out top academic talent for their long-term potential.
#     *   **Is there a strong mentorship program in place?** If so, Bob's potential could be nurtured effectively. If not, Alice's self-sufficiency might be preferred.
#     *   **What is the current team's composition?** Does the team need more practical doers, or more critical thinkers to challenge existing norms?

# 4.  **Long-Term Growth Potential:**
#     *   While Alice has more current experience, Bob's academic background might position him for quicker advancement into leadership or more complex roles in the long run, given the right development. I'd assess their expressed career aspirations during the interview.

# 5.  **Interview Performance & Cultural Fit:**
#     *   Beyond the resume, how did each candidate perform in interviews?
#     *   Did they demonstrate strong communication, problem-solving, and interpersonal skills?
#     *   Did their values align with our company culture?
#     *   What were their responses to behavioral questions regarding teamwork, handling challenges, and learning new things?

# 6.  **References and Portfolio/Projects:**
#     *   What do their references say about their performance, work ethic, and specific contributions?
#     *   If applicable, does either candidate have a portfolio or specific project examples that stand out?

# **My Recommendation (as a Senior HR Assistant):**

# Given the limited information, **I would not make a definitive hire recommendation yet.** Instead, I would recommend the following to the hiring manager:
# 1.  **Conduct a more in-depth, structured interview:** Design behavioral and situational questions specifically tailored to the crucial skills and challenges of the new role.
# 2.  **Administer a skill assessment (if applicable):** For technical roles, a practical test could reveal who possesses the most relevant skills.
# 3.  **Deep dive into past projects/achievements:** Ask Alice to describe specific projects she led or contributed to, detailing her responsibilities and impact. Ask Bob about academic projects, research, or work experiences where he applied his analytical skills.
# 4.  **Reference Checks:** These are vital for both candidates to validate their experience, work ethic, and cultural fit.

# **Hypothetical Scenarios for a Final Decision:**
# *   **If the role is for a highly specialized, hands-on, and immediate-impact position with little room for error (e.g., Senior Systems Administrator maintaining critical infrastructure),** I would likely lean towards **Alice**. Her 5 years of practical experience suggest she's seen more scenarios and can handle them independently.
# *   **If the role is for a strategic analyst, a junior research and development position, or a role focused on innovation and future growth (e.g., Data Scientist working on new algorithms),** I would lean towards **Bob**. His prestigious academic background, combined with 3 years of experience, suggests strong analytical abilities and a high capacity for learning and contributing new ideas, even if his practical experience is slightly less.
# Ultimately, the goal is to find the best fit for *this specific role* at *this specific time* within our *company culture*. It's not about which candidate is "better" in a vacuum, but which one aligns most closely with the comprehensive needs of the position.