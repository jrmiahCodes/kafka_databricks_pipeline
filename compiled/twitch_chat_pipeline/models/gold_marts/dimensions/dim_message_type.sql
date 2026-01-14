

select
    message_type,
    description
from (
    select 'EMOTE_ONLY'       as message_type, 'Messages containing only emotes' as description union all
    select 'LOW_EFFORT',       'Very short or low-entropy messages' union all
    select 'REPETITIVE_SPAM',  'Messages with excessive repeated characters' union all
    select 'ENGAGED_CHAT',     'Messages showing meaningful engagement' union all
    select 'OTHER',            'Messages not fitting other categories'
)