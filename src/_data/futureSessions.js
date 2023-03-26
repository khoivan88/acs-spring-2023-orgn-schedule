/** Every timestamp is in UTC time */
const now = new Date();
// const now = new Date('2022-03-20T20:00:00.000Z');    //! for testing
// Offset current time by 4 hours
const nowOffset = new Date(now.getTime() - 4 * 60 * 60 * 1000);

const allSessions = require('./acs_spring2023_orgn.json')

const futureSessions = allSessions.filter(session => {
    const sessionDate = new Date(session.starting_datetime);
    return sessionDate >= nowOffset;
});
// console.log(nowOffset);
// console.log(futureSessions.length);

module.exports = futureSessions;
