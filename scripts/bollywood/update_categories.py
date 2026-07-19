import re

content = open('scripts/wiki_scraper/south_asian/bollywood.py').read()

filmfare_new = '''
        ("Best Action", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Action", "Technical"),
        ("Best Art Direction", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Art_Direction", "Technical"),
        ("Best Background Score", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Background_Score", "Music"),
        ("Best Choreography", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Choreography", "Technical"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Cinematography", "Technical"),
        ("Best Costume Design", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Costume_Design", "Technical"),
        ("Best Dialogue", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Dialogue", "Writing"),
        ("Best Editing", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Editing", "Technical"),
        ("Best Lyricist", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Lyricist", "Music"),
        ("Best Sound Design", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Sound_Design", "Technical"),
        ("Best Special Effects", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Special_Effects", "Technical"),
        ("Best Performance in a Negative Role", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Performance_in_a_Negative_Role", "Acting"),
        ("Best Performance in a Comic Role", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Performance_in_a_Comic_Role", "Acting"),
        ("Critics Award for Best Film", "https://en.wikipedia.org/wiki/Filmfare_Critics_Award_for_Best_Film", "Film"),
        ("Critics Award for Best Actor", "https://en.wikipedia.org/wiki/Filmfare_Critics_Award_for_Best_Actor", "Acting"),
        ("Critics Award for Best Actress", "https://en.wikipedia.org/wiki/Filmfare_Critics_Award_for_Best_Actress", "Acting"),
        ("Lifetime Achievement Award", "https://en.wikipedia.org/wiki/Filmfare_Lifetime_Achievement_Award", "Honorary"),
'''

iifa_new = '''
        ("Best Performance in a Negative Role", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Performance_in_a_Negative_Role", "Acting"),
        ("Best Performance in a Comic Role", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Performance_in_a_Comic_Role", "Acting"),
        ("Best Music Director", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Music_Director", "Music"),
        ("Best Lyricist", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Lyricist", "Music"),
        ("Best Male Playback Singer", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Male_Playback_Singer", "Music"),
        ("Best Female Playback Singer", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Female_Playback_Singer", "Music"),
        ("Best Story", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Story", "Writing"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Screenplay", "Writing"),
        ("Best Dialogue", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Dialogue", "Writing"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Cinematography", "Technical"),
        ("Best Choreography", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Choreography", "Technical"),
        ("Best Editing", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Editing", "Technical"),
        ("Best Sound Recording", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Sound_Recording", "Technical"),
        ("Best Sound Re-Recording", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Sound_Re-Recording", "Technical"),
        ("Best Special Effects", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Special_Effects", "Technical"),
        ("Best Art Direction", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Art_Direction", "Technical"),
        ("Best Action", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Action", "Technical"),
        ("Best Makeup", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Makeup", "Technical"),
        ("Best Costume Design", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Costume_Design", "Technical"),
'''

national_new = '''
        ("Best Children's Film", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Children%27s_Film", "Film"),
        ("Best Music Direction", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Music_Direction", "Music"),
        ("Best Male Playback Singer", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Male_Playback_Singer", "Music"),
        ("Best Female Playback Singer", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Female_Playback_Singer", "Music"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Cinematography", "Technical"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Screenplay", "Writing"),
        ("Best Audiography", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Audiography", "Technical"),
        ("Best Editing", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Editing", "Technical"),
        ("Best Art Direction", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Art_Direction", "Technical"),
        ("Best Costume Design", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Costume_Design", "Technical"),
        ("Best Make-up Artist", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Make-up_Artist", "Technical"),
        ("Best Choreography", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Choreography", "Technical"),
        ("Best Special Effects", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Special_Effects", "Technical"),
        ("Best Lyrics", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Lyrics", "Music"),
        ("Best Child Artist", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Child_Artist", "Acting"),
'''

screen_new = '''
        ("Best Supporting Actor", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Supporting_Actor", "Acting"),
        ("Best Supporting Actress", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Supporting_Actress", "Acting"),
        ("Best Actor in a Negative Role", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Actor_in_a_Negative_Role", "Acting"),
        ("Best Actor in a Comic Role", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Actor_in_a_Comic_Role", "Acting"),
        ("Best Music Director", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Music_Director", "Music"),
        ("Best Male Playback", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Male_Playback", "Music"),
        ("Best Female Playback", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Female_Playback", "Music"),
        ("Best Lyricist", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Lyricist", "Music"),
        ("Best Story", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Story", "Writing"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Screenplay", "Writing"),
        ("Best Dialogue", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Dialogue", "Writing"),
        ("Best Editing", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Editing", "Technical"),
        ("Best Cinematography", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Cinematography", "Technical"),
'''

zee_new = '''
        ("Best Actor in a Supporting Role", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Actor_in_a_Supporting_Role_%E2%80%93_Male", "Acting"),
        ("Best Actress in a Supporting Role", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Actor_in_a_Supporting_Role_%E2%80%93_Female", "Acting"),
        ("Best Performance in a Negative Role", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Performance_in_a_Negative_Role", "Acting"),
        ("Best Performance in a Comic Role", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Performance_in_a_Comic_Role", "Acting"),
        ("Best Music Director", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Music_Director", "Music"),
        ("Best Lyricist", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Lyricist", "Music"),
        ("Best Playback Singer Male", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Playback_Singer_%E2%80%93_Male", "Music"),
        ("Best Playback Singer Female", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Playback_Singer_%E2%80%93_Female", "Music"),
        ("Best Story", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Story", "Writing"),
        ("Best Screenplay", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Screenplay", "Writing"),
        ("Best Dialogue", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Dialogue", "Writing"),
'''

content = content.replace('("Best Debut Female", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Debut_Female", "Acting"),\\n    ]', '("Best Debut Female", "https://en.wikipedia.org/wiki/Filmfare_Award_for_Best_Debut_Female", "Acting"),\\n' + filmfare_new + '    ]')
content = content.replace('("Best Supporting Actress", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Supporting_Actress", "Acting"),\\n    ]', '("Best Supporting Actress", "https://en.wikipedia.org/wiki/IIFA_Award_for_Best_Supporting_Actress", "Acting"),\\n' + iifa_new + '    ]')
content = content.replace('("Best Popular Film", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Popular_Film", "Film"),\\n    ]', '("Best Popular Film", "https://en.wikipedia.org/wiki/National_Film_Award_for_Best_Popular_Film", "Film"),\\n' + national_new + '    ]')
content = content.replace('("Best Actress", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Actress", "Acting"),\\n    ]', '("Best Actress", "https://en.wikipedia.org/wiki/Screen_Award_for_Best_Actress", "Acting"),\\n' + screen_new + '    ]')
content = content.replace('("Best Actress", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Actor_Female", "Acting"),\\n    ]', '("Best Actress", "https://en.wikipedia.org/wiki/Zee_Cine_Award_for_Best_Actor_Female", "Acting"),\\n' + zee_new + '    ]')

open('scripts/wiki_scraper/south_asian/bollywood.py', 'w').write(content)
print('Updated bollywood.py')
