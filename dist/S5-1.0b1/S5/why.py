import random
from random import randint, choice


def why():
    THEANSWER = Why()
    THEANSWER.disp()


class Why:
    Authors = ['Owen']
    Names = ['Ellie', 'Joe', 'Morgan', 'James', 'Isaac', 'David', 'Owen the Kiwi', 'Tommy', 'Brain', 'Flanders', 'Nick',
             'Luke', 'Ella', 'Anith', 'Ved', 'Ioan', 'Jack', 'Dylan', 'Connor', 'Tommy', 'Ben']

    def disp(self):
        n = random.randint(0, 100)
        if n < 10:
            output = self.quotes()
        elif n < 20:
            output = self.special_case()
        elif n < 50:
            output = self.phrase()
        else:
            output = self.sentence()
        print(output.capitalize())

    def special_case(self):
        sc_list = [f"Because {choice(self.Authors)} said so.",
                   'how should I know?',
                   'the computer did it.',
                   'don''t ask!',
                   'the customer is always right.',
                   ]
        if random.randint(0, 100) == 42:
            return f'in the beginning, God created the heavens and the earth, and {", and ".join(self.Authors)} created S5'
        else:
            return random.choice(sc_list)

    def phrase(self):
        ph_list = [
            # f"The answer is {self.noun()}",
            f'for the {self.nounded_verb()} {self.prepositional_phrase()}',
            f'to {self.present_verb()} {self.obj()}.',
            f'because {self.sentence()}'
        ]
        return choice(ph_list)

    def present_verb(self):
        pres_v_lst = [
            'fool',
            'please',
            'satisfy',
            'butter up'
        ]
        return choice(pres_v_lst)
    def preposition(self):
        prepo_lst = [
            'of',
            'from'
        ]
        return choice(prepo_lst)

    def prepositional_phrase(self):
        prepo_ph_lst = [
            f"{self.preposition()} {self.article()} {self.noun_phrase()}",
            f"{self.preposition()} {self.noun()}",
            f"{self.preposition()} {self.accusative_pronoun()}"
        ]
        return choice(prepo_ph_lst)

    def nounded_verb(self):
        nv_lst = ['love', 'approval']
        return choice(nv_lst)

    def proper_noun(self):
        return (choice(self.Names + self.Authors))

    def subject(self):
        sbj_lst = [
            self.proper_noun(),
            self.nominative_pronoun(),
        ]
        return choice(sbj_lst)

    def nominative_pronoun(self):
        nompro_list = ['I', 'you', 'he', 'she', 'they']
        return choice(nompro_list)

    def sentence(self):
        return f'{self.subject()} {self.predicate()}.'

    def predicate(self):
        predic_lst = [
            f"{self.transitive_verb()} {self.obj()}",
            f"{self.intransitive_verb()}"
        ]
        return choice(predic_lst)

    def transitive_verb(self):
        trans_v_lst = [
            'threatened',
            'told',
            'asked',
            'helped',
            'obeyed'
        ]
        return choice(trans_v_lst)

    def intransitive_verb(self):
        intran_v_lst = [
            'insisted on it',
            'suggested it',
            'told me to',
            'wanted it',
            'knew it was a good idea',
            'wanted it that way'
        ]
        return choice(intran_v_lst)

    def obj(self):
        obj_lst = [
            self.accusative_pronoun(),
            f"{self.article()} {self.noun_phrase()}",
        ]
        return choice(obj_lst)

    def article(self):
        art_lst = [
            'the', 'some', 'a'
        ]
        return choice(art_lst)

    def noun_phrase(self):
        noun_ph_lst = [
            f"{self.noun()}", f"{self.noun()}", f"{self.noun()}", f"{self.noun()}", f"{self.noun()}", f"{self.noun()}",
            f"{self.adjective_phrase()} {self.noun()}", f"{self.adjective_phrase()} {self.noun()}"
        ]
        if random.randint(0, 4) == 3:
            return f"{self.adjective_phrase()} {self.noun_phrase()}"
        return choice(noun_ph_lst)

    def noun(self):
        noun_lst = [
            "engineer",
            "chief engineer",
            "fresher",
            "kid",
            "dad",
            "programmer",
            "badger's ringpiece",
            "rollhoop"
        ]
        return choice(noun_lst)

    def adjective_phrase(self):
        adj_ph_lst = [
            f"{self.adjective()}",
            f"{self.adjective()}",
            f"{self.adjective()}",
            f"{self.adverb()} {self.adjective()}",
        ]
        if random.randint(0, 6) == 1:
            return f"{self.adjective_phrase()} and {self.adjective_phrase()}"
        return choice(adj_ph_lst)

    def accusative_pronoun(self):
        accu_pron_lst = [
            'me',
            'all',
            'her',
            'him',
            'they'
        ]
        return choice(accu_pron_lst)

    def adverb(self):
        adv_lst = [
            'very',
            'not very',
            'not excessively',
            'just about',
            'nearly'
        ]
        return choice(adv_lst)

    def adjective(self):
        adj_list = [
            'tall',
            'bald',
            'young',
            'smart',
            'rich',
            'terrified',
            'good',
            "itsy bitsy tiny winey light grey"
        ]
        return choice(adj_list)

    def quotes(self):
        quotes = [
            "Life is worse now I have no chicken.",
            "There are new fresh coming in, you don’t need to bully me anymore!",
            "It’s a can. It should be in the CAN-opy",
            "Carbon’s meant to be black so it's fine.",
            "Why would Deacs think…?",
            "But I can see Joe being a special case",
            "Why won’t you let me mate",
            "I’m trying to do Maths",
            "I do like a slap",
            "Run my babies, run!"
        ]
        return choice(quotes)


if __name__ == '__main__':
    for i in range(100):
        why()
